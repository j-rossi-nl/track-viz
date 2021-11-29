"""Create a heatmap from the tracking information, superimposes on a background image."""
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yaml


def heatmap(track: Path, config: Path, img: Path) -> None:
    """Create heatmap."""
    df = pd.read_csv(track, parse_dates=["time"])
    with config.open("r") as src:
        conf = yaml.safe_load(src)

    img = mpimg.imread(conf["heatmap"]["background"]["image"])

    min_lon, max_lon = (
        conf["heatmap"]["background"]["min_lon"],
        conf["heatmap"]["background"]["max_lon"],
    )
    min_lat, max_lat = (
        conf["heatmap"]["background"]["min_lat"],
        conf["heatmap"]["background"]["max_lat"],
    )

    df["lon_x"] = df["lon"].apply(
        lambda x: img.shape[0] * (x - min_lon) / (max_lon - min_lon)
    )
    df["lat_y"] = df["lat"].apply(
        lambda y: img.shape[1] * (y - min_lat) / (max_lat - min_lat)
    )

    fig, ax = plt.subplots(figsize=(10, 10))

    # Draw the heatmap
    sns.kdeplot(
        data=df,
        x="lon_x",
        y="lat_y",
        levels=conf["heatmap"]["plot"]["levels"],
        fill=True,
        cmap=conf["heatmap"]["plot"]["colormap"],
        ax=ax,
    )

    # Draw the satellite image
    ax.imshow(img, extent=[0, img.shape[0], 0, img.shape[1]])

    # Disappear ticks / labels on axes
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_xticks([])
    ax.set_yticks([])

    # Save
    fig.savefig(img)
