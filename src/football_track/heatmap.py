"""Create a heatmap from the tracking information, superimposes on a background image."""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yaml

from .input_file import TrackingColumn


def heatmap_from_dataframe(track: pd.DataFrame, config: Path) -> mpl.figure.Figure:
    """Create heatmap."""
    with config.open("r") as src:
        conf = yaml.safe_load(src)

    img_data = plt.imread(conf["heatmap"]["background"]["image"])

    min_lon, max_lon = (
        conf["heatmap"]["background"]["min_lon"],
        conf["heatmap"]["background"]["max_lon"],
    )
    min_lat, max_lat = (
        conf["heatmap"]["background"]["min_lat"],
        conf["heatmap"]["background"]["max_lat"],
    )

    track["lon_x"] = track[TrackingColumn.LONGITUDE].apply(
        lambda x: img_data.shape[0] * (x - min_lon) / (max_lon - min_lon)
    )
    track["lat_y"] = track[TrackingColumn.LATITUDE].apply(
        lambda y: img_data.shape[1] * (y - min_lat) / (max_lat - min_lat)
    )

    fig, ax = plt.subplots(figsize=(10, 10))

    # Draw the heatmap
    sns.kdeplot(
        data=track,
        x="lon_x",
        y="lat_y",
        levels=conf["heatmap"]["plot"]["levels"],
        fill=True,
        cmap=conf["heatmap"]["plot"]["colormap"],
        ax=ax,
    )

    # Draw the satellite image
    ax.imshow(img_data, extent=[0, img_data.shape[0], 0, img_data.shape[1]])

    # Disappear ticks / labels on axes
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_xticks([])
    ax.set_yticks([])

    return fig


def heatmap(track: Path, config: Path) -> mpl.figure.Figure:
    """Create heatmap."""
    df = pd.read_csv(track, parse_dates=["time"])
    return heatmap_from_dataframe(track=df, config=config)
