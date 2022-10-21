"""Run a Flask web server to create heatmap and speed graph."""
import datetime as dt
import json
import os
import string
from base64 import b64encode
from base64 import urlsafe_b64encode
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from secrets import choice
from secrets import token_hex
from secrets import token_urlsafe
from tempfile import gettempdir
from typing import Any
from typing import Dict
from typing import List
from urllib.parse import urlencode

import flask.typing as ft
from fitbit import ApiClient
from fitbit import Configuration
from fitbit.api import ActivityApi
from fitbit.api import AuthApi
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from werkzeug.utils import secure_filename

from .heatmap import heatmap_from_dataframe
from .input_file import gpx_to_dataframe
from .input_file import tcx_to_dataframe
from .speed import altair_plot_pace
from .speed import plotly_plot_trace


app = Flask(__name__)
app.secret_key = token_urlsafe(64)
ALLOWED_EXTENSIONS = {".tcx", ".gpx"}
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4MB
app.config["UPLOAD_FOLDER"] = gettempdir()

UNRESERVED = string.ascii_letters + string.digits + "-._~"


def _allowed_file(filename: str) -> bool:
    return Path(filename).suffix in ALLOWED_EXTENSIONS


@app.route("/heatmap", methods=["GET", "POST"])
def create_heatmap() -> ft.ResponseReturnValue:
    """Handles incoming activity file and create heatmap."""
    if request.method == "POST" or "tcx_file" in session:
        if "tcx_file" in session:
            fpath = Path(session.pop("tcx_file"))
            session.modified = True
        else:
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

        fig = heatmap_from_dataframe(track=track)
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
    if request.method == "POST" or "tcx_file" in session:
        if "tcx_file" in session:
            fpath = Path(session.pop("tcx_file"))
            session.modified = True
        else:
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

        specjson = altair_plot_pace(track=track)
        fpath.unlink()

        mapjson = plotly_plot_trace(track=track)

        return render_template(
            "show_graph.html",
            page_title="Speed Graphs",
            context={"vega_data_json": specjson, "plot_run_trace": mapjson},
        )
    else:
        return render_template("upload_speed.html")


@app.route("/fitbitauthorize", methods=["GET"])
def fitbit_authorize() -> ft.ResponseReturnValue:
    """Get Authorization from Fitbit."""
    code_verifier = "".join(choice(UNRESERVED) for _ in range(64))
    code_challenge = urlsafe_b64encode(
        sha256(code_verifier.encode("utf-8")).digest()
    ).decode("utf-8")[:-1]

    params = {
        "client_id": os.getenv("FITBIT_CLIENT_ID"),
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": "location activity heartrate",
    }

    session["code_verifier"] = code_verifier
    session["origin"] = request.args.get("page")
    session.modified = True
    authorization_url = "https://www.fitbit.com/oauth2/authorize?" + urlencode(params)
    return redirect(authorization_url)


@app.route("/fitbitcallback", methods=["GET"])
def fitbit_callback() -> ft.ResponseReturnValue:
    """Registered Fitbit App Callback URL.

    When requesting authorization, Fitbit calls with ?code=xxx
    """
    code = request.args.get("code")
    code_verifier = session["code_verifier"]

    auth = AuthApi()
    auth.oauth_token(
        client_id=os.getenv("FITBIT_CLIENT_ID"),
        code=code,
        code_verifier=code_verifier,
        grant_type="authorization_code",
        authorization="Basic "
        + b64encode(
            f'{os.getenv("FITBIT_CLIENT_ID")}:{os.getenv("FITBIT_SECRET")}'.encode()
        ).decode("utf-8"),
    )

    auth_data = json.loads(auth.api_client.last_response.data)
    session["fitbit_auth"] = auth_data
    session.modified = True

    return redirect("/fitbitlistruns")


@app.route("/fitbitlistruns", methods=["GET"])
def fitbit_listruns() -> ft.ResponseReturnValue:
    """Present a list of downloadable runs."""
    config = Configuration()
    config.access_token = session["fitbit_auth"]["access_token"]

    api_client = ApiClient(configuration=config)
    api_client.set_default_header(
        header_name="X-Fitbit-Subscriber-Id",
        header_value=session["fitbit_auth"]["user_id"],
    )

    activity = ActivityApi(api_client=api_client)
    activity.get_activities_log_list(
        before_date=(dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%d"),
        sort="desc",
        offset=0,
        limit=20,
    )

    response = json.loads(api_client.last_response.data)
    runs: List[Dict[str, Any]] = list(
        filter(lambda a: a["activityName"] in ["Run", "Walk"], response["activities"])
    )

    hrefs = [f'/fitbitloadrun?logid={r["logId"]}' for r in runs]

    dates = [
        f"{dt.datetime.fromisoformat(r['startTime']).strftime('%A %-d %B %Y, %H:%M')}"
        for r in runs
    ]

    def _duration(milliseconds: int) -> str:
        secs = (milliseconds // 1000) % 60
        mins = (milliseconds // (1000 * 60)) % 60
        hours = (milliseconds // (1000 * 60 * 60)) % 24
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    durations = [_duration(r["duration"]) for r in runs]

    return render_template(
        "show_fitbit_runs.html",
        context={
            "runs": [
                {"href": h, "date": d, "duration": dd}
                for h, d, dd in zip(hrefs, dates, durations)
            ]
        },
    )


@app.route("/fitbitloadrun", methods=["GET"])
def fitbit_loadrun() -> ft.ResponseReturnValue:
    """Download TCX from Fitbit, and open the page."""
    config = Configuration()
    config.access_token = session["fitbit_auth"]["access_token"]

    api_client = ApiClient(configuration=config)
    api_client.set_default_header(
        header_name="X-Fitbit-Subscriber-Id",
        header_value=session["fitbit_auth"]["user_id"],
    )

    activity = ActivityApi(api_client=api_client)
    activity.get_activities_log_list(
        before_date=dt.datetime.now().strftime("%Y-%m-%d"),
        sort="asc",
        offset=0,
        limit=20,
    )

    activity.get_activities_tcx(request.args.get("logid"))

    fpath = Path(app.config["UPLOAD_FOLDER"]) / f"{token_hex(16)}.tcx"

    with fpath.open("wb") as out:
        out.write(api_client.last_response.data)

    session["tcx_file"] = str(fpath)
    session.modified = True
    return redirect(f'/{session.get("origin")}')


# @app.route("/test")
# def test():
#     return render_template(
#         "show_fitbit_runs.html",
#         context={
#             "runs": [{"href": "ouh la la", "date": "trop vite", "duration": "pas mal"}]
#         },
#     )


def run_webserver(host: str, port: int) -> None:
    """Run webserver."""
    app.run(host=host, port=port, debug=False)
