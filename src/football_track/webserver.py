import os
import io

from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from secrets import token_hex

from .input_file import tcx_to_dataframe, gpx_to_dataframe
from .heatmap import heatmap
from .speed import plot_speed

from pathlib import Path

app = Flask(__name__)
app.config["ALLOWED_EXTENSIONS"] = {"tcx", "gpx"}
app.config["UPLOAD_FOLDER"] = "upload"


@app.route('/heatmap', methods=['GET', 'POST'])
def create_heatmap():
    if request.method == 'POST':
        f = request.files['file']
        fpath = Path(app.config["UPLOAD_FOLDER"]) / f"{token_hex(8)}_{secure_filename(f.filename)}"
        f.save(fpath)

        csv_path = fpath.with_suffix(".csv")
        suffix = fpath.suffix
        if suffix == ".tcx":
            tcx_to_dataframe(tcx=fpath, to=csv_path)
        elif suffix == ".gpx":
            gpx_to_dataframe(gpx=fpath, to=csv_path)
        else:
            raise ValueError(f"Wrong suffix {suffix}, expected one of {app.config['ALLOWED_EXTENSIONS']}")

        heatmap_path = fpath.with_suffix(".jpg")
        heatmap(track=csv_path, config=Path("static/heatmap.yml"), jpg=heatmap_path)

        bytes = heatmap_path.read_bytes()
        stream = io.BytesIO(bytes)

        fpath.unlink()
        csv_path.unlink()
        heatmap_path.unlink()

        return send_file(stream, mimetype="image/jpeg")
    else:
        return render_template('upload_heatmap.html')


@app.route('/speed', methods=['GET', 'POST'])
def create_speed_plot():
    if request.method == 'POST':
        f = request.files['file']
        fpath = Path(app.config["UPLOAD_FOLDER"]) / f"{token_hex(8)}_{secure_filename(f.filename)}"
        f.save(fpath)

        csv_path = fpath.with_suffix(".csv")
        suffix = fpath.suffix
        if suffix == ".tcx":
            tcx_to_dataframe(tcx=fpath, to=csv_path)
        elif suffix == ".gpx":
            gpx_to_dataframe(gpx=fpath, to=csv_path)
        else:
            raise ValueError(f"Wrong suffix {suffix}, expected one of {app.config['ALLOWED_EXTENSIONS']}")

        speed_path = fpath.with_suffix(".jpg")
        plot_speed(track=csv_path, jpg=speed_path)

        bytes = speed_path.read_bytes()
        stream = io.BytesIO(bytes)

        fpath.unlink()
        csv_path.unlink()
        speed_path.unlink()

        return send_file(stream, mimetype="image/jpeg")
    else:
        return render_template('upload_speed.html')


def run_webserver():
    app.run(debug=False)
