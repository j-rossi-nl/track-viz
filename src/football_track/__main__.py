"""Command-line interface."""
import click

from typing import Any
from pathlib import Path

from .tcx import tcx_to_dataframe

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
    "--to-csv",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, path_type=Path)
)
def tcx_to_csv(**kwargs: Any) -> None:
    tcx_to_dataframe(**kwargs)


if __name__ == "__main__":
    main(prog_name="football-track")  # pragma: no cover
