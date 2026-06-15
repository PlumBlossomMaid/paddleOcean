"""ocean CLI — unified command-line interface.

Usage:
    ocean train --config config.yaml
    ocean cloud upload repo_id path
    ocean cloud download repo_id
    ocean model export --checkpoint ckpt.pdparams --format onnx
"""

import click


@click.group()
def cli():
    """ocean: PaddlePaddle framework, batteries included."""


# Import subcommands to register them
from ocean.cli.cloud import cloud  # noqa: E402, F401
from ocean.cli.model import model  # noqa: E402, F401
from ocean.cli.train import train  # noqa: E402, F401

cli.add_command(train)
cli.add_command(model)
cli.add_command(cloud)


def main():
    """Entry point for `python -m ocean.cli` and console_scripts."""
    cli()
