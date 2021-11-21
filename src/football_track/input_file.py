"""Process a TCX or GPX file into a dataframe."""
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

import pandas as pd
from defusedxml.ElementTree import parse


def _data_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"])
    return df


def tcx_to_dataframe(tcx: Path, to: Path) -> None:
    """Process a TCX file."""
    tree = parse(str(tcx))
    ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}

    trackpoints = tree.findall(".//tcx:Trackpoint", ns)
    n_trackpoints = len(trackpoints)
    print(f"Tracking {n_trackpoints} trackpoints")
    data = []
    for point in trackpoints:
        sample = {}
        sample["time"] = point.find(".//tcx:Time", ns).text
        sample["lat"] = float(point.find(".//tcx:LatitudeDegrees", ns).text)
        sample["lon"] = float(point.find(".//tcx:LongitudeDegrees", ns).text)
        sample["bpm"] = int(point.find(".//tcx:HeartRateBpm/tcx:Value", ns).text)
        data.append(sample)

    df = _data_to_dataframe(data)
    df.to_csv(to, index=False)


def gpx_to_dataframe(gpx: Path, to: Path) -> None:
    """Process GPX file."""
    tree = parse(str(gpx))
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    trackpoints = tree.findall(".//gpx:trkpt", ns)
    n_trackpoints = len(trackpoints)
    print(f"Tracking {n_trackpoints} trackpoints")
    data = []
    for point in trackpoints:
        sample = {}
        sample["time"] = point.find(".//gpx:time", ns).text
        sample["lat"] = float(point.get("lat"))
        sample["lon"] = float(point.get("lon"))
        data.append(sample)

    df = _data_to_dataframe(data)
    df.to_csv(to, index=False)
