"""Test cases for the __main__ module."""
import pytest
from click.testing import CliRunner

from football_track import main


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


def test_main(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main)
    assert result.exit_code == 0


def test_tcx(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(
        main, ["tcx-to-csv", "--tcx", "tests/sample_tcx.tcx", "--to", "/dev/null"]
    )
    assert result.exit_code == 0


def test_gpx(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(
        main, ["gpx-to-csv", "--gpx", "tests/sample_gpx.gpx", "--to", "/dev/null"]
    )
    assert result.exit_code == 0
