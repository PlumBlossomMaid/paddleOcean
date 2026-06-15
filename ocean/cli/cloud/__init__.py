"""ocean cloud — AI Studio integration."""

import click

from ocean.cli.cloud import _config  # noqa: F401 — expose config for overrides
from ocean.cli.cloud.auth import login, logout
from ocean.cli.cloud.download import download
from ocean.cli.cloud.job import job
from ocean.cli.cloud.upload import upload


@click.group()
def cloud():
    """AI Studio cloud operations.

    Manage datasets, models, and training jobs on Baidu AI Studio.
    """


cloud.add_command(login)
cloud.add_command(logout)
cloud.add_command(upload)
cloud.add_command(download)
cloud.add_command(job)
