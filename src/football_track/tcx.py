import pandas as pd
from lxml import etree
from pathlib import Path


def tcx_to_dataframe(tcx: Path, to_csv: Path) -> None:
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

    df = pd.DataFrame(data)
    df.to_csv(to_csv)
