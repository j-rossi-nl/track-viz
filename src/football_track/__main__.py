"""Command-line interface."""
import click

from typing import Any
from pathlib import Path

from .input_file import tcx_to_dataframe
from .input_file import gpx_to_dataframe
from .speed import plot_speed as command_plot_speed

@click.group()
@click.version_option()
def main() -> None:
    """Football Track."""


@main.command()
@click.option(
    "--tcx",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path)
)
@click.option(
    "--to",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, path_type=Path)
)
def tcx_to_csv(**kwargs: Any) -> None:
    tcx_to_dataframe(**kwargs)


@main.command()
@click.option(
    "--gpx",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path)
)
@click.option(
    "--to",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, path_type=Path)
)
def gpx_to_csv(**kwargs: Any) -> None:
    gpx_to_dataframe(**kwargs)


@main.command()
@click.option(
    "--track",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path)
)
@click.option(
    "--jpg",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, path_type=Path)
)
def plot_speed(**kwargs: Any) -> None:
    command_plot_speed(**kwargs)


if __name__ == "__main__":
    main(prog_name="football-track")  # pragma: no cover
