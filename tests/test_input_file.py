"""Test cases for the __main__ module."""
from pathlib import Path

from track_viz import gpx_to_dataframe
from track_viz import tcx_to_dataframe


def test_gpx() -> None:
    """It exits with a status code of zero."""
    df = gpx_to_dataframe(Path("tests/sample_gpx.gpx"))
    assert df.shape[0] == 5


def test_tcx() -> None:
    """It exits with a status code of zero."""
    df = tcx_to_dataframe(Path("tests/sample_tcx.tcx"))
    assert df.shape[0] == 4
