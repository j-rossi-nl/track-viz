"""Create a speed graph from a tracking dataframe."""
from pathlib import Path

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from geopy import distance

mpl.use("Agg")
sns.set_theme(
    style="whitegrid",
    palette="pastel",
    rc={"axes.facecolor": "#2590eb", "figure.facecolor": "#2590eb"},
)


def _track_2_speeds(df: pd.DataFrame) -> pd.DataFrame:
    movements = df.copy(deep=True)
    movements["delta_time"] = df["time"].diff()
    for coord in ["lon", "lat"]:
        movements[f"prev_{coord}"] = movements[coord].shift()
    movements["delta_alt_m"] = movements["alt"].diff()
    movements = movements.dropna()

    # geopy gives only geodesic distance
    movements["ground_distance_m"] = movements.apply(
        lambda x: distance.distance(
            (x["lat"], x["lon"]), (x["prev_lat"], x["prev_lon"])
        ).meters,
        axis=1,
    )

    # accounting for altitude change, using Pythagorus
    movements["distance_m"] = (
        movements["ground_distance_m"] ** 2 + movements["delta_alt_m"] ** 2
    ) ** 0.5

    movements["speed_ms"] = movements["distance_m"] / movements["delta_time"].dt.seconds
    movements["speed_kmh"] = movements["speed_ms"] * 3.6

    movements["delta_speed_ms"] = movements["speed_ms"].diff()
    movements = movements.dropna()

    movements["acceleration_ms2"] = (
        movements["delta_speed_ms"] / movements["delta_time"].dt.seconds
    )

    # only pd.timestamp  has strftime, this is a dirty trick
    # noinspection PyTypeChecker
    movements["elapsed_time"] = (
        pd.Timestamp("2021-01-01 00:00") + movements["delta_time"].cumsum()
    )

    movements.set_index("elapsed_time", inplace=True)
    return movements


def plot_speed(track: Path, img: Path) -> None:
    """Create the speed plot."""
    df = pd.read_csv(track, parse_dates=["time"])
    movements = _track_2_speeds(df)

    fig, ax = plt.subplots(figsize=(16, 8))
    movements.plot.area(y="speed_kmh", ax=ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%M:%S"))
    fig.savefig(img)


def plot_speed_moving_avg(track: Path, img: Path) -> None:
    """Create the speed plot."""
    df = pd.read_csv(track, parse_dates=["time"])
    movements = _track_2_speeds(df)
    movements["speed_moving_avg_1min"] = movements["speed_kmh"].rolling("60s").mean()

    fig, ax = plt.subplots(figsize=(16, 8))
    movements.plot.area(y="speed_moving_avg_1min", ax=ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%M:%S"))
    fig.savefig(img)


def plot_acceleration(track: Path, img: Path) -> None:
    """Create the speed plot."""
    df = pd.read_csv(track, parse_dates=["time"])
    movements = _track_2_speeds(df)

    fig, ax = plt.subplots(figsize=(16, 8))
    movements.plot.area(y="acceleration_ms2", stacked=False, ax=ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%M:%S"))
    fig.savefig(img)
