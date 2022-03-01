"""Create a speed graph from a tracking dataframe."""
from pathlib import Path

import altair as alt
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from geopy import distance

from .input_file import TrackingColumn

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
    """Transform tracking information to time series of speed and other metrics.

    List of fields in the movements dataframe:
    * delta_time: time difference between one sample and the previous one
    * prev_lon, prev_lat: longitude / latitude of previous tracking point
    * delta_alt_m: altitude difference in meters between current sample and previous sample
    * elapsed_time: timestamp of a tracking point, considering the run started on Jan 1 2021 at 00:00
    * ground_distance_m: distance over earth surface covered between previous point and current point, in meters
    * distance_m: distance in meters between previous point and current point, taking altitude difference into account
    * speed_ms: speed at the current point in meters per second
    * speed_kmh: speed in kilometers per hour
    * speed_moving_avg_1min: moving average of the speed over the last minute, in kilometers per hour
    * delta_speed_ms: change in speed in meters per second
    * delta_moving_avg_1min: change in moving average in kilometers per hour
    * acceleration_ms2: acceleration in meters per square meters
    * use_point: bool indicates whether the point is "usable"

    The sampling frequency is identified as the most frequent time difference between 2 samples. Any time this time
    difference is more than 2 times this sampling frequency, we mark the first point AFTER the gap with FALSE in
    field "use_point".
    """
    movements = df.copy(deep=True)
    movements["delta_time"] = df[TrackingColumn.TIME].diff()
    for coord in [TrackingColumn.LONGITUDE, TrackingColumn.LATITUDE]:
        movements[f"prev_{coord}"] = movements[coord].shift()
    movements["delta_alt_m"] = movements[TrackingColumn.ALTITUDE].diff()
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
            (x[TrackingColumn.LATITUDE], x[TrackingColumn.LONGITUDE]),
            (
                x[f"prev_{TrackingColumn.LATITUDE}"],
                x[f"prev_{TrackingColumn.LONGITUDE}"],
            ),
        ).meters,
        axis=1,
    )

    # accounting for altitude change, using Pythagorus
    movements["distance_m"] = (
        movements["ground_distance_m"] ** 2 + movements["delta_alt_m"] ** 2
    ) ** 0.5

    movements["speed_ms"] = (
        movements["distance_m"] / movements["delta_time"].dt.total_seconds()
    )
    movements["speed_kmh"] = movements["speed_ms"] * 3.6
    movements["speed_moving_avg_1min"] = movements["speed_kmh"].rolling("60s").mean()

    movements["delta_speed_ms"] = movements["speed_ms"].diff()
    movements["delta_moving_avg_1min"] = movements["speed_moving_avg_1min"].diff()
    movements = movements.dropna()

    movements["acceleration_ms2"] = (
        movements["delta_speed_ms"] / movements["delta_time"].dt.total_seconds()
    )

    # Identify missing points in the data
    freq_s = movements["delta_time"].dt.seconds.value_counts().index[0]
    movements["use_point"] = movements["delta_time"].dt.seconds.apply(
        lambda x: x <= 2 * freq_s
    )

    for measure in ["speed_moving_avg_1min", TrackingColumn.ALTITUDE]:
        movements[measure] = movements[["use_point", measure]].apply(
            lambda x: x[measure] if x["use_point"] else np.nan, axis=1
        )

    movements["run_distance_km"] = movements["distance_m"].cumsum() / 1000.0
    movements["speed_minpkm"] = 60.0 / movements["speed_kmh"]
    movements["elapsed_minutes"] = (
        movements["time"] - movements["time"].min()
    ).dt.total_seconds() / 60.0

    return movements


def plot_movement_field(movements: pd.DataFrame, mvt_field: str) -> mpl.figure.Figure:
    """Standard plot for 1 field of the movements dataframe."""
    fig, ax = plt.subplots()
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


def altair_plot_pace(track: pd.DataFrame) -> str:
    """Prepare an altair viz for instantaneous speed and elevation.

    Returns a Vega-Lite JSON spec file.
    """
    movs = track_2_movements(track)
    source = movs[["run_distance_km", "speed_minpkm", "alt", "elapsed_minutes"]]
    brush = alt.selection(type="interval", encodings=["x"], name="selector")

    pace = (
        alt.Chart(source)
        .mark_area(
            line={"color": "darkgreen"},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="white", offset=0),
                    alt.GradientStop(color="darkgreen", offset=1),
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0,
            ),
        )
        .transform_loess(loess="speed_minpkm", on="run_distance_km", bandwidth=0.02)
        .transform_calculate(
            pace="datum.speed_minpkm",
            pace_txt="format(floor(datum.pace), 'd') + ':' + format(floor((datum.pace - floor(datum.pace)) * 60), '02d')",
        )
        .encode(
            x=alt.X("run_distance_km:Q", title="Distance (km)"),
            y=alt.Y("speed_minpkm:Q", title="Pace (min/km)"),
            tooltip=[
                alt.Tooltip("run_distance_km", title="Distance (km)", format=".1f"),
                alt.Tooltip("pace_txt:N", title="Pace (min/km)"),
            ],
        )
        .add_selection(brush)
    )

    average_pace = (
        alt.Chart(source)
        .transform_filter(brush)
        .mark_rule(color="#636363", strokeDash=[10, 10])
        .transform_aggregate(
            maxd="max(run_distance_km)",
            mind="min(run_distance_km)",
            maxt="max(elapsed_minutes)",
            mint="min(elapsed_minutes)",
        )
        .transform_calculate(
            pace=(alt.datum.maxt - alt.datum.mint) / (alt.datum.maxd - alt.datum.mind),
            pace_txt="format(floor(datum.pace), 'd') + ':' + format(floor((datum.pace - floor(datum.pace)) * 60), '02d')",
        )
        .encode(
            y="pace:Q",
            size=alt.SizeValue(3),
            tooltip=[
                alt.Tooltip("pace_txt:N", title="Average Pace in Selection (min/km)")
            ],
        )
    )

    average_pace_text = (
        alt.Chart(source)
        .mark_text(
            align="center",
            baseline="bottom",
            fontSize=12,
            dx=5,
            dy=-5,
            fontWeight="bold",
            color="darkgreen",
        )
        .transform_filter(brush)
        .transform_aggregate(
            maxd="max(run_distance_km)",
            mind="min(run_distance_km)",
            maxt="max(elapsed_minutes)",
            mint="min(elapsed_minutes)",
        )
        .transform_calculate(
            pace=(alt.datum.maxt - alt.datum.mint) / (alt.datum.maxd - alt.datum.mind),
            delta_d=alt.datum.maxd - alt.datum.mind,
            midx=(alt.datum.maxd + alt.datum.mind) / 2,
            pace_txt="'Distance (m): ' + format(floor(datum.delta_d * 1000), 'd') + "
            "' / Pace (min/km): ' + format(floor(datum.pace), 'd') + ':'"
            " + format(floor((datum.pace - floor(datum.pace)) * 60), '02d')",
        )
        .encode(
            text="pace_txt:N",
            x="midx:Q",
            y=alt.value(5),
            opacity=alt.condition(brush, alt.OpacityValue(0), alt.OpacityValue(1)),
        )
    )

    # Draw the elevation profile
    elevation = (
        alt.Chart(source)
        .mark_area(line={"color": "brown"}, color="#d8b5a5")
        .encode(
            x="run_distance_km:Q",
            y=alt.Y(
                "alt:Q",
                scale=alt.Scale(
                    domain=[
                        source["alt"].min(),
                        source["alt"].max()
                        + 2 * (source["alt"].max() - source["alt"].min()),
                    ]
                ),
            ),
        )
        .transform_loess(loess="alt", on="run_distance_km", bandwidth=0.02)
    )

    # Put the five layers into a chart and bind the data
    layers = (
        alt.layer(pace + average_pace + average_pace_text, elevation)
        .resolve_scale(y="independent")
        .properties(width="container", height="container")
        .configure_axisLeft(titleColor="darkgreen", labelColor="darkgreen")
        .configure_axisRight(titleColor="brown", labelColor="brown")
    )

    jsondumps: str = layers.to_json()
    return jsondumps
