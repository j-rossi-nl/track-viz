"""Run a Flask web server to create heatmap and speed graph."""
import io
from pathlib import Path
from secrets import token_hex
from tempfile import gettempdir

import flask.typing as ft
from flask import Flask
from flask import Markup  # type: ignore
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from werkzeug.utils import secure_filename

from .heatmap import heatmap
from .input_file import gpx_to_dataframe
from .input_file import tcx_to_dataframe
from .speed import plot_acceleration
from .speed import plot_speed
from .speed import plot_speed_moving_avg

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

        csv_path = fpath.with_suffix(".csv")
        suffix = fpath.suffix
        if suffix == ".tcx":
            tcx_to_dataframe(tcx=fpath, to=csv_path)
        elif suffix == ".gpx":
            gpx_to_dataframe(gpx=fpath, to=csv_path)
        else:
            raise ValueError(
                f"Wrong suffix {suffix}, expected one of {app.config['ALLOWED_EXTENSIONS']}"
            )

        heatmap_path = fpath.with_suffix(".jpg")
        heatmap(track=csv_path, config=Path("static/heatmap.yml"), jpg=heatmap_path)

        img_bytes = heatmap_path.read_bytes()
        stream = io.BytesIO(img_bytes)

        fpath.unlink()
        csv_path.unlink()
        heatmap_path.unlink()

        return send_file(stream, mimetype="image/jpeg")
    else:
        return render_template("upload_heatmap.html")


@app.route("/speed", methods=["GET", "POST"])
def create_speed_plot() -> ft.ResponseReturnValue:
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

        csv_path = fpath.with_suffix(".csv")
        suffix = fpath.suffix
        if suffix == ".tcx":
            tcx_to_dataframe(tcx=fpath, to=csv_path)
        elif suffix == ".gpx":
            gpx_to_dataframe(gpx=fpath, to=csv_path)
        else:
            raise ValueError(
                f"Wrong suffix {suffix}, expected one of {app.config['ALLOWED_EXTENSIONS']}"
            )

        speed_path = fpath.with_suffix(".svg")
        plot_speed(track=csv_path, img=speed_path)
        speed_xml = speed_path.read_text()

        plot_speed_moving_avg(track=csv_path, img=speed_path)
        speed_moving_avg_xml = speed_path.read_text()

        plot_acceleration(track=csv_path, img=speed_path)
        acceleration_xml = speed_path.read_text()

        fpath.unlink()
        csv_path.unlink()
        speed_path.unlink()

        return render_template(
            "show_graph.html",
            page_title="Speed Graphs",
            img_speed=Markup(speed_xml),
            img_speed_moving_avg=Markup(speed_moving_avg_xml),
            img_acceleration=Markup(acceleration_xml),
        )
    else:
        return render_template("upload_speed.html")


def run_webserver(host: str, port: int) -> None:
    """Run webserver."""
    app.run(host=host, port=port, debug=False)
