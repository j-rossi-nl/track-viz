"""Create a speed graph from a tracking dataframe."""
from pathlib import Path

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from geopy import distance

mpl.use("Agg")
sns.set_theme(
    style="whitegrid",
    palette="colorblind",
    rc={
        "axes.facecolor": "#F5FFFA",
        "figure.facecolor": "#F5FFFA",
        "figure.figsize": (20, 10),
    },
)
plt.rcParams["figure.figsize"] = (20, 10)


def track_2_movements(df: pd.DataFrame) -> pd.DataFrame:
    """Transform tracking information to time series of speed and other metrics."""
    movements = df.copy(deep=True)
    movements["delta_time"] = df["time"].diff()
    for coord in ["lon", "lat"]:
        movements[f"prev_{coord}"] = movements[coord].shift()
    movements["delta_alt_m"] = movements["alt"].diff()
    movements = movements.dropna()

    # only pd.timestamp  has strftime, this is a dirty trick
    # noinspection PyTypeChecker
    movements["elapsed_time"] = (
        pd.Timestamp("2021-01-01 00:00") + movements["delta_time"].cumsum()
    )
    movements = movements.set_index("elapsed_time")

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
    movements["speed_moving_avg_1min"] = movements["speed_kmh"].rolling("60s").mean()

    movements["delta_speed_ms"] = movements["speed_ms"].diff()
    movements["delta_moving_avg_1min"] = movements["speed_moving_avg_1min"].diff()
    movements = movements.dropna()

    movements["acceleration_ms2"] = (
        movements["delta_speed_ms"] / movements["delta_time"].dt.seconds
    )

    # Identify missing points in the data
    freq_s = movements["delta_time"].dt.seconds.value_counts().index[0]
    movements["use_point"] = movements["delta_time"].dt.seconds.apply(
        lambda x: x <= 2 * freq_s
    )

    for measure in ["speed_moving_avg_1min", "alt"]:
        movements[measure] = movements[["use_point", measure]].apply(
            lambda x: x[measure] if x["use_point"] else np.nan, axis=1
        )

    return movements


def plot_movement_field(movements: pd.DataFrame, mvt_field: str) -> mpl.figure.Figure:
    """Standard plot for 1 field of the movements dataframe."""
    fig, ax = plt.subplots(figsize=(16, 8))
    movements.plot.area(y=mvt_field, stacked=False, ax=ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%M:%S"))
    return fig


def _from_track_to_plot(track: Path, mvt_field: str) -> mpl.figure.Figure:
    df = pd.read_csv(track, parse_dates=["time"])
    movements = track_2_movements(df)
    return plot_movement_field(movements=movements, mvt_field=mvt_field)


def plot_speed(track: Path) -> mpl.figure.Figure:
    """Create the speed plot."""
    return _from_track_to_plot(track=track, mvt_field="speed_kmh")


def plot_speed_moving_avg(track: Path) -> mpl.figure.Figure:
    """Create the speed plot."""
    return _from_track_to_plot(track=track, mvt_field="speed_moving_avg_1min")


def plot_acceleration(track: Path) -> mpl.figure.Figure:
    """Create the speed plot."""
    return _from_track_to_plot(track=track, mvt_field="acceleration_ms2")


def web_plot_speed_elevation(track: pd.DataFrame) -> mpl.figure.Figure:
    """Create plot for website with both speed and elevation."""
    movs = track_2_movements(track)
    unused_points = movs.index[~movs["use_point"]]
    unused_times = []
    for pt in unused_points:
        loc = movs.index.get_loc(pt)
        unused_times.append(
            (movs.index[loc - 1], movs.index[min(movs.shape[0] - 1, loc + 1)])
        )

    fig, ax = plt.subplots()
    movs.plot.line(
        y=["speed_moving_avg_1min", "alt"],
        secondary_y=["alt"],
        ax=ax,
        linewidth=2,
        color=[sns.color_palette()[0], sns.color_palette()[1]],
        zorder=0,
    )
    movs.plot.area(
        y=["speed_moving_avg_1min", "alt"],
        secondary_y=["alt"],
        stacked=False,
        ax=ax,
        linewidth=0,
        color=[sns.color_palette()[0], sns.color_palette()[1]],
        alpha=0.2,
        legend=False,
        zorder=1,
    )

    for u in unused_times:
        ax.fill_between(
            [u[0], u[1]],
            ax.get_ylim()[0],
            ax.get_ylim()[1],
            facecolor="lightgrey",
            hatch="//",
            zorder=2,
        )

    ax.grid(visible=False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%M:%S"))

    # Elevation graph within the bottom third of the image
    ax.right_ax.set_ylim(
        movs["alt"].min() - 0.5,
        movs["alt"].max() + 2 * (movs["alt"].max() - movs["alt"].min()),
    )
    ax.right_ax.grid(visible=False)
    return fig


def web_plot_speed_climb_kde(track: pd.DataFrame) -> mpl.figure.Figure:
    """Create plot for website for KDE with speed and elevation."""
    movs = track_2_movements(track)
    movs = movs.replace([np.inf, -np.inf], np.nan)
    movs = movs.dropna()
    movs["climb"] = (
        np.sign(movs["delta_alt_m"])
        .replace(0.0, 1.0)
        .map({1.0: "Uphill", -1.0: "Downhill"})
        .astype("category")
    )
    fig, ax = plt.subplots()
    sns.kdeplot(x="speed_kmh", fill=True, hue="climb", data=movs, cut=0, ax=ax)
    ax.grid(visible=False)
    ax.set_ylabel("")
    ax.set_yticks([])
    ax.get_legend().set_title("TERRAIN")
    return fig
