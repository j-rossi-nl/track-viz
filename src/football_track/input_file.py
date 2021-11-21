import pandas as pd
from lxml import etree
from pathlib import Path

from typing import List, Dict, Any

def _data_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"])
    return df


def tcx_to_dataframe(tcx: Path, to: Path) -> None:
    tree = etree.parse(str(tcx))
    laps = tree.xpath("//*[name()='TrainingCenterDatabase']/*[name()='Activities']/*[name()='Activity']/*[name()='Lap']")
    assert len(laps) == 1
    game = laps[0]
    trackpoints = game.xpath("*[name()='Track']/*[name()='Trackpoint']")
    n_trackpoints = len(trackpoints)
    print(f"Tracking {n_trackpoints} trackpoints = {n_trackpoints // 60:02d}m{n_trackpoints % 60:02d}s")
    data = []
    for point in trackpoints:
        sample = {}
        sample["time"] = point.xpath("*[name()='Time']")[0].text
        sample["lat"] = float(point.xpath("*[name()='Position']/*[name()='LatitudeDegrees']")[0].text)
        sample["lon"] = float(point.xpath("*[name()='Position']/*[name()='LongitudeDegrees']")[0].text)
        sample["bpm"] = int(point.xpath("*[name()='HeartRateBpm']/*[name()='Value']")[0].text)
        data.append(sample)

    df = _data_to_dataframe(data)
    df.to_csv(to, index=False)


def gpx_to_dataframe(gpx: Path, to: Path) -> None:
    tree = etree.parse(str(gpx))
    trackpoints = tree.xpath("/*[name()='gpx']/*[name()='trk']/*[name()='trkseg']/*[name()='trkpt']")
    n_trackpoints = len(trackpoints)
    print(f"Tracking {n_trackpoints} trackpoints")
    data = []
    for point in trackpoints:
        sample = {}
        sample["time"] = point.xpath("*[name()='time']")[0].text
        sample["lat"] = float(point.get("lat"))
        sample["lon"] = float(point.get("lon"))
        data.append(sample)

    df = _data_to_dataframe(data)
    df.to_csv(to, index=False)