"""Command-line interface."""
from pathlib import Path
from typing import Any

import click

from .heatmap import heatmap as do_heatmap
from .input_file import gpx_to_dataframe
from .input_file import tcx_to_dataframe
from .speed import plot_speed as plot_speed
from .webserver import run_webserver


@click.group()
@click.version_option()
def main() -> None:
    """Football Track."""


@main.command()
@click.option(
    "--tcx",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
    ),
)
@click.option(
    "--to",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, writable=True, path_type=Path
    ),
)
def tcx_to_csv(**kwargs: Any) -> None:
    """TCX file to CSV dataframe."""
    tcx_to_dataframe(**kwargs)


@main.command()
@click.option(
    "--gpx",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
    ),
)
@click.option(
    "--to",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, writable=True, path_type=Path
    ),
)
def gpx_to_csv(**kwargs: Any) -> None:
    """GPX file to CSV dataframe."""
    gpx_to_dataframe(**kwargs)


@main.command()
@click.option(
    "--track",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
    ),
)
@click.option(
    "--jpg",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, writable=True, path_type=Path
    ),
)
def speed(**kwargs: Any) -> None:
    """CVS dataframe to Speed plot."""
    plot_speed(**kwargs)


@main.command()
@click.option(
    "--track",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
    ),
)
@click.option(
    "--config",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
    ),
)
@click.option(
    "--jpg",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, writable=True, path_type=Path
    ),
)
def heatmap(**kwargs: Any) -> None:
    """CSV dataframe to heatmap."""
    do_heatmap(**kwargs)


@main.command()
@click.option("--host", type=str, default="127.0.0.1")
@click.option("--port", type=int, default=5000)
def flask(**kwargs: Any) -> None:
    """Have a web server GUI."""
    run_webserver(**kwargs)


if __name__ == "__main__":
    main(prog_name="football-track")  # pragma: no cover
