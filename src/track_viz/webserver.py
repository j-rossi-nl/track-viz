"""Run a Flask web server to create heatmap and speed graph."""
from base64 import b64encode
from io import BytesIO
from io import StringIO
from pathlib import Path
from secrets import token_hex
from tempfile import gettempdir

import flask.typing as ft
from flask import Flask
from flask import Markup  # type: ignore
from flask import redirect
from flask import render_template
from flask import request
from werkzeug.utils import secure_filename

from .heatmap import heatmap_from_dataframe
from .input_file import gpx_to_dataframe
from .input_file import tcx_to_dataframe
from .speed import web_plot_speed_climb_kde
from .speed import web_plot_speed_elevation


app = Flask(__name__)
ALLOWED_EXTENSIONS = {".tcx", ".gpx"}
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4MB
app.config["UPLOAD_FOLDER"] = gettempdir()


def _allowed_file(filename: str) -> bool:
    return Path(filename).suffix in ALLOWED_EXTENSIONS


@app.route("/heatmap", methods=["GET", "POST"])
def create_heatmap() -> ft.ResponseReturnValue:
    """Handles incoming activity file and create heatmap."""
    if request.method == "POST":
        f = request.files["file"]

        if f.filename is None or not _allowed_file(f.filename):
            return redirect(request.url)

        fpath = (
            Path(app.config["UPLOAD_FOLDER"])
            / f"{token_hex(8)}_{secure_filename(f.filename)}"
        )
        f.save(fpath)

        suffix = fpath.suffix
        if suffix == ".tcx":
            track = tcx_to_dataframe(tcx=fpath)
        elif suffix == ".gpx":
            track = gpx_to_dataframe(gpx=fpath)
        else:
            raise ValueError(
                f"Wrong suffix {suffix}, expected one of {app.config['ALLOWED_EXTENSIONS']}"
            )

        fig = heatmap_from_dataframe(track=track, config=Path("static/heatmap.yml"))
        img_bytes = BytesIO()
        fig.savefig(img_bytes, format="jpg")
        img_b64bytes = b64encode(img_bytes.getvalue()).decode("utf-8")

        fpath.unlink()

        return render_template("show_heatmap.html", img_data=img_b64bytes)
    else:
        return render_template("upload_heatmap.html")


@app.route("/speed", methods=["GET", "POST"])
def create_speed_plots() -> ft.ResponseReturnValue:
    """Handles incoming activity file and create speed graph."""
    if request.method == "POST":
        f = request.files["file"]

        if f.filename is None or not _allowed_file(f.filename):
            return redirect(request.url)

        fpath = (
            Path(app.config["UPLOAD_FOLDER"])
            / f"{token_hex(8)}_{secure_filename(f.filename)}"
        )
        f.save(fpath)

        suffix = fpath.suffix
        if suffix == ".tcx":
            track = tcx_to_dataframe(tcx=fpath)
        elif suffix == ".gpx":
            track = gpx_to_dataframe(gpx=fpath)
        else:
            raise ValueError(
                f"Wrong suffix {suffix}, expected one of {app.config['ALLOWED_EXTENSIONS']}"
            )

        fig = web_plot_speed_elevation(track=track)
        speed_terrain_xml = StringIO()
        fig.savefig(speed_terrain_xml, format="svg")

        fig = web_plot_speed_climb_kde(track=track)
        speed_terrain_kde_xml = StringIO()
        fig.savefig(speed_terrain_kde_xml, format="svg")

        fpath.unlink()

        return render_template(
            "show_graph.html",
            page_title="Speed Graphs",
            img_speed_terrain=Markup(speed_terrain_xml.getvalue()),
            img_speed_terrain_kde=Markup(speed_terrain_kde_xml.getvalue()),
        )
    else:
        return render_template("upload_speed.html")


def run_webserver(host: str, port: int) -> None:
    """Run webserver."""
    app.run(host=host, port=port, debug=False)
