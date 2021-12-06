"""Process a TCX or GPX file into a dataframe."""
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import numpy as np
import pandas as pd
from defusedxml.ElementTree import parse


class TrackingColumn:
    """Names of columns in a tracking dataframe."""

    TIME = "time"
    LATITUDE = "lat"
    LONGITUDE = "lon"
    ALTITUDE = "alt"
    HEARTBEAT = "bpm"


def _float(x: Optional[str]) -> float:
    if x is not None:
        return float(x)
    else:
        return np.nan


def _data_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(data)
    df[TrackingColumn.TIME] = pd.to_datetime(df[TrackingColumn.TIME])
    return df


def tcx_to_dataframe(tcx: Path) -> pd.DataFrame:
    """Process a TCX file."""
    tree = parse(str(tcx))
    ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}

    trackpoints = tree.findall(".//tcx:Trackpoint", ns)
    n_trackpoints = len(trackpoints)
    print(f"Tracking {n_trackpoints} trackpoints")
    data = []
    for point in trackpoints:
        sample = {
            TrackingColumn.TIME: point.find(".//tcx:Time", ns).text,
            TrackingColumn.LATITUDE: _float(
                point.find(".//tcx:LatitudeDegrees", ns).text
            ),
            TrackingColumn.LONGITUDE: _float(
                point.find(".//tcx:LongitudeDegrees", ns).text
            ),
            TrackingColumn.ALTITUDE: _float(
                point.find(".//tcx:AltitudeMeters", ns).text
            ),
            TrackingColumn.HEARTBEAT: int(
                point.find(".//tcx:HeartRateBpm/tcx:Value", ns).text
            ),
        }
        data.append(sample)

    df = _data_to_dataframe(data)
    return df


def gpx_to_dataframe(gpx: Path) -> pd.DataFrame:
    """Process GPX file."""
    tree = parse(str(gpx))
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    trackpoints = tree.findall(".//gpx:trkpt", ns)
    n_trackpoints = len(trackpoints)
    print(f"Tracking {n_trackpoints} trackpoints")
    data = []
    for point in trackpoints:
        sample = {
            TrackingColumn.TIME: point.find(".//gpx:time", ns).text,
            TrackingColumn.LATITUDE: _float(point.get("lat")),
            TrackingColumn.LONGITUDE: _float(point.get("lon")),
            TrackingColumn.ALTITUDE: _float(point.find(".//gpx:ele", ns).text),
        }
        data.append(sample)

    df = _data_to_dataframe(data)
    return df
