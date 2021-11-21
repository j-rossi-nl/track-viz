"""Create a speed graph from a tracking dataframe."""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from geopy import distance


def plot_speed(track: Path, jpg: Path) -> None:
    """Create the spped plot."""
    df = pd.read_csv(track, parse_dates=["time"])
    lats = df["lat"].values
    lons = df["lon"].values
    times = df["time"].values

    data = []
    for time, lat, lon, prev_time, prev_lat, prev_lon in zip(
        times[1:], lats[1:], lons[1:], times, lats, lons
    ):
        data.append(
            {
                "delta_time": time - prev_time,
                "lat": lat,
                "prev_lat": prev_lat,
                "lon": lon,
                "prev_lon": prev_lon,
            }
        )

    movements = pd.DataFrame(data)
    movements["distance_m"] = movements.apply(
        lambda x: distance.distance(
            (x["lat"], x["lon"]), (x["prev_lat"], x["prev_lon"])
        ).meters,
        axis=1,
    )
    movements["speed_kmh"] = (
        3.6 * movements["distance_m"] / movements["delta_time"].dt.seconds
    )

    # only pd.timestamp  has strftime, this is a dirty trick
    movements["elapsed_time"] = (
        pd.Timestamp("2021-01-01 00:00") + movements["delta_time"].cumsum()
    )

    sns.set_theme()
    fig, ax = plt.subplots(figsize=(40, 4))
    movements.plot.area(x="elapsed_time", y="speed_kmh", ax=ax)
    ax.grid(visible=True)
    ax.set_ylim(0, 16)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%M:%S"))
    fig.savefig(jpg)
