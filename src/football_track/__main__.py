"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Football Track."""


if __name__ == "__main__":
    main(prog_name="football-track")  # pragma: no cover
