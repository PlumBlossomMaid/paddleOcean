"""cloud delete — delete files from AI Studio repos.

Usage (CLI):
    ocean cloud delete user/repo path/to/file

Usage (Python API):
    >>> from ocean.cloud import delete_file
    >>> delete_file("user/repo", "path/to/file", token="...")
"""

from typing import Optional

import click

from ocean.cli.cloud import _config
from ocean.cli.cloud.auth import get_token
from ocean.cli.cloud.upload import _check_file_exists, _git_api


def delete_file(
    repo_id: str,
    path_in_repo: str,
    token: Optional[str] = None,
    repo_type: str = "dataset",
    revision: str = "master",
    commit_message: Optional[str] = None,
) -> dict:
    """Delete a file from an AI Studio repo.

    Args:
        repo_id: ``username/repo-name``.
        path_in_repo: Path to the file in the repo.
        token: AI Studio access token. Falls back to ``ocean config`` if None.
        repo_type: ``"dataset"`` or ``"model"``.
        revision: Branch name (default: ``master``).
        commit_message: Optional commit message.

    Returns:
        API response dict.
    """
    _config.validate_repo_id(repo_id)
    if token is None:
        token = get_token()
    if commit_message is None:
        commit_message = f"Delete {path_in_repo}"

    # Check file exists and get SHA
    sha = _check_file_exists(repo_id, path_in_repo, revision, token)
    if sha is None:
        raise click.ClickException(f"File not found: {path_in_repo}")

    # Add repo_type prefix if model
    api_path = f"/api/v1/repos/{repo_id}/contents/{path_in_repo}?ref={revision}"
    payload = {
        "sha": sha,
        "message": commit_message,
    }

    return _git_api("DELETE", api_path, token, data=payload)


# ── CLI ──────────────────────────────────────────────────────────────


@click.command(name="delete")
@click.argument("repo_id", metavar="REPO_ID")
@click.argument("path_in_repo", metavar="PATH_IN_REPO")
@click.option("--repo-type", default="dataset", type=click.Choice(["model", "dataset"]))
@click.option("--revision", default="master", help="Branch name.")
@click.option("--token", default=None, help="AI Studio access token.")
@click.option("-m", "--message", default=None, help="Commit message.")
def delete(repo_id, path_in_repo, repo_type, revision, token, message):
    """Delete a file from an AI Studio repo.

    REPO_ID: Format ``username/repo-name``.

    PATH_IN_REPO: Path to the file to delete.
    """
    delete_file(
        repo_id=repo_id,
        path_in_repo=path_in_repo,
        token=token,
        repo_type=repo_type,
        revision=revision,
        commit_message=message,
    )
    click.echo(f"  ✅ Deleted {path_in_repo} from {repo_id}")
