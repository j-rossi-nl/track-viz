"""Create a heatmap from the tracking information, superimposes on a background image."""
import os
from dataclasses import dataclass
from io import BytesIO
from math import atan
from math import exp
from math import floor
from math import log
from math import log2
from math import pi
from math import tan
from pathlib import Path
from pprint import pprint
from typing import Any
from typing import Dict
from typing import Protocol
from typing import Tuple
from urllib.request import urlopen

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .input_file import TrackingColumn


@dataclass
class DegreesCoordinates:
    """Geodesic coordinates LATITUDE / LONGITUDE."""

    lat: float
    lon: float


@dataclass
class BBox:
    """Bounding Box."""

    southwest: DegreesCoordinates
    northeast: DegreesCoordinates


@dataclass
class PixelCoordinates:
    """Cartesian coordinates X / Y."""

    x: float
    y: float


# Convert geographical coordinates to pixels
# https://en.wikipedia.org/wiki/Web_Mercator_projection
# Note on mapbox API:
# The world map is obtained with lat=lon=0, w=h=512, zoom=0
#
# Therefore:
ZOOM0_SIZE = 512


# Geo-coordinate in degrees => Pixel coordinate
def _g2p(dcoords: DegreesCoordinates, zoom: int) -> PixelCoordinates:
    return PixelCoordinates(
        x=ZOOM0_SIZE * (2 ** zoom) * (1 + dcoords.lon / 180) / 2,
        y=ZOOM0_SIZE
        / (2 * pi)
        * (2 ** zoom)
        * (pi - log(tan(pi / 4 * (1 + dcoords.lat / 90)))),
    )


# Pixel coordinate => geo-coordinate in degrees
def _p2g(pcoords: PixelCoordinates, zoom: int) -> DegreesCoordinates:
    return DegreesCoordinates(
        lat=(
            atan(exp(pi - pcoords.y / ZOOM0_SIZE * (2 * pi) / (2 ** zoom))) / pi * 4 - 1
        )
        * 90,
        lon=(pcoords.x / ZOOM0_SIZE * 2 / (2 ** zoom) - 1) * 180,
    )


# bbox = (left, bottom, right, top) in degrees
def _get_map_by_bbox(bbox: BBox) -> Tuple[Dict[str, Any], BBox]:
    # The region of interest in geo-coordinates in degrees
    # For example, bbox = [120.2206, 22.4827, 120.4308, 22.7578]
    left, bottom, right, top = (
        bbox.southwest.lon,
        bbox.southwest.lat,
        bbox.northeast.lon,
        bbox.northeast.lat,
    )

    # Sanity check
    good_inputs = (-90 <= bottom < top <= 90) and (-180 <= left < right <= 180)
    if not good_inputs:
        raise ValueError("Incorrect inputs.")

    # Rendered image map size in pixels as it should come from MapBox (no retina)
    (w, h) = (1024, 1024)

    # The center point of the region of interest
    (lat, lon) = ((top + bottom) / 2, (left + right) / 2)

    # Reduce precision of (lat, lon) to increase cache hits
    # All of this was so easy with lambda, but no... flake8 required no lambda
    # and mypy wants everything typed, and Callable does not support optional arguments
    class _Snap(Protocol):
        def __call__(self, x: float, scale: float = 1.0) -> float:
            ...

    def _snap_to_dyadic(a: float, b: float) -> _Snap:
        def _actual_snap(
            x: float, scale: float = (2 ** floor(log2(abs(b - a) / 4)))
        ) -> float:
            return round(x / scale) * scale

        return _actual_snap

    lat = _snap_to_dyadic(bottom, top)(lat)
    lon = _snap_to_dyadic(left, right)(lon)

    ref_point_in_bbox = (bottom < lat < top) and (left < lon < right)
    if not ref_point_in_bbox:
        raise ValueError("Reference point not inside the region of interest")

    # Look for appropriate zoom level to cover the region of interest
    zoom: int
    for zoom in range(24, -1, -1):
        # Center point in pixel coordinates at this zoom level
        p0: PixelCoordinates = _g2p(DegreesCoordinates(lat=lat, lon=lon), zoom=zoom)

        # The "container" geo-region that the downloaded map would cover
        northwest = _p2g(PixelCoordinates(x=p0.x - w / 2, y=p0.y - h / 2), zoom=zoom)
        southeast = _p2g(PixelCoordinates(x=p0.x + w / 2, y=p0.y + h / 2), zoom=zoom)

        # Would the map cover the region of interest?
        if (northwest.lon <= left < right <= southeast.lon) and (
            southeast.lat <= bottom < top <= northwest.lat
        ):
            # Collect all parameters
            params = {
                "style": "satellite-v9",
                "lat": lat,
                "lon": lon,
                "token": os.getenv("MAPBOX_TOKEN", "no-token"),
                "zoom": zoom,
                "w": w,
                "h": h,
                "retina": "@2x",
            }

            pprint(params)

            return params, BBox(
                southwest=DegreesCoordinates(lat=southeast.lat, lon=northwest.lon),
                northeast=DegreesCoordinates(lat=northwest.lat, lon=southeast.lon),
            )

    raise ValueError("Does not compute")


def heatmap_from_dataframe(track: pd.DataFrame) -> mpl.figure.Figure:
    """Create heatmap."""
    # Find the bounding box from all point coordinates
    lons, lats = track[TrackingColumn.LONGITUDE], track[TrackingColumn.LATITUDE]
    min_lon, min_lat = min(lons), min(lats)
    max_lon, max_lat = max(lons), max(lats)

    bbox = BBox(
        southwest=DegreesCoordinates(lat=min_lat, lon=min_lon),
        northeast=DegreesCoordinates(lat=max_lat, lon=max_lon),
    )

    params, final_bbox = _get_map_by_bbox(bbox=bbox)

    # Get data from mapbox
    url_template = "https://api.mapbox.com/styles/v1/mapbox/{style}/static/{lon},{lat},{zoom}/{w}x{h}{retina}?access_token={token}&attribution=false&logo=false"  # noqa
    mapbox_url = url_template.format(**params)

    with urlopen(mapbox_url) as api_call:  # noqa
        data = api_call.read()

    img_data = plt.imread(BytesIO(data), format="jpg")

    left, bottom, right, top = (
        final_bbox.southwest.lon,
        final_bbox.southwest.lat,
        final_bbox.northeast.lon,
        final_bbox.northeast.lat,
    )
    track["lon_x"] = track[TrackingColumn.LONGITUDE].apply(
        lambda x: img_data.shape[0] * (x - left) / (right - left)
    )
    track["lat_y"] = track[TrackingColumn.LATITUDE].apply(
        lambda y: img_data.shape[1] * (y - bottom) / (top - bottom)
    )

    fig, ax = plt.subplots(figsize=(10, 10))

    # Draw the heatmap
    sns.kdeplot(
        data=track,
        x="lon_x",
        y="lat_y",
        levels=100,
        fill=True,
        cmap="rocket_r",
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
    return heatmap_from_dataframe(track=df)
