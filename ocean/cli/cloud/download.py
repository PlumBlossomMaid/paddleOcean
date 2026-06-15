"""cloud download — download files from AI Studio.

Supports regular and LFS files (model checkpoints, large datasets).

Usage:
    ocean cloud download user/repo path/to/file --repo-type model
"""

import os
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import click
import requests
from tqdm import tqdm

from ocean.cli.cloud import _config
from ocean.cli.cloud.auth import get_token
from ocean.cli.cloud.upload import _header_fill


def _download_file(url: str, dest: str, token: str, desc: str = ""):
    """Download a single file with progress bar."""
    headers = {
        "Authorization": f"token {token}",
        "SDK-Version": "ocean-0.1",
    }
    resp = requests.get(url, headers=headers, stream=True, timeout=3600)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    with open(dest, "wb") as f:
        pbar = tqdm(total=total, unit="B", unit_scale=True, desc=desc or Path(dest).name) if total and desc else None
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            if pbar:
                pbar.update(len(chunk))
        if pbar:
            pbar.close()
    return dest


def _download_with_lfs_check(repo_id: str, file_info: dict, dest: str, token: str, revision: str = "master"):
    """Download a file, using the Gitea media API for LFS objects."""
    name = file_info["name"]

    # Use the media API endpoint (handles LFS content transparently)
    user_name, repo_name = repo_id.split("/")
    git_host = os.getenv("STUDIO_GIT_HOST", _config.GIT_HOST)
    url = (
        f"{git_host}/api/v1/repos/{quote(user_name, safe='')}/{quote(repo_name, safe='')}/media/{quote(name, safe='')}"
    )
    if revision != "master":
        url += f"?ref={quote(revision, safe='')}"

    _download_file(url, dest, token, desc=name)


@click.command()
@click.argument("repo_id")
@click.argument("path_in_repo", required=False, default=None)
@click.option("--local-dir", default=".", help="Local directory to save files.")
@click.option("--repo-type", type=click.Choice(["model", "dataset"]), default="dataset")
@click.option("--revision", default="master", help="Branch name.")
@click.option("--token", default=None, help="AI Studio access token.")
@click.option("--include", multiple=True, help="Glob patterns to include.")
@click.option("--exclude", multiple=True, help="Glob patterns to exclude.")
def download(
    repo_id: str,
    path_in_repo: Optional[str],
    local_dir: str,
    repo_type: str,
    revision: str,
    token: Optional[str],
    include,
    exclude,
):
    """Download files from AI Studio.

    REPO_ID: Format ``username/repo-name``.

    Examples:

        ocean cloud download PlumBlossom/MyDataset

        ocean cloud download PlumBlossom/MyModel ./model.pdparams --repo-type model
    """
    token = token or get_token()
    _config.validate_repo_id(repo_id)

    dest = Path(local_dir).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    git_host = os.getenv("STUDIO_GIT_HOST", _config.GIT_HOST)

    if path_in_repo:
        # Download single file — get file info from API
        url = f"{git_host}/api/v1/repos/{repo_id}/contents/{path_in_repo}?ref={revision}"
        resp = requests.get(url, headers=_header_fill(token), timeout=30)
        resp.raise_for_status()
        file_info = resp.json()
        out = str(dest / Path(path_in_repo).name)
        _download_with_lfs_check(repo_id, file_info, out, token, revision)
        click.echo(f"✅ Downloaded to {out}")
    else:
        # Download all files via API listing
        url = f"{git_host}/api/v1/repos/{repo_id}/contents?ref={revision}"
        resp = requests.get(url, headers=_header_fill(token), timeout=30)
        resp.raise_for_status()
        items = resp.json()

        if isinstance(items, list):
            for item in items:
                if item["type"] == "file":
                    dl_path = str(dest / item["name"])
                    _download_with_lfs_check(repo_id, item, dl_path, token, revision)
        elif isinstance(items, dict):
            dl_path = str(dest / items["name"])
            _download_with_lfs_check(repo_id, items, dl_path, token, revision)

    click.echo(f"✅ Downloaded from {repo_id}")


# ── Public Python API ────────────────────────────────────────────────


def download_file(
    repo_id: str,
    path_in_repo: str,
    local_dir: str = ".",
    repo_type: str = "dataset",
    revision: str = "master",
    token: Optional[str] = None,
) -> str:
    """Download a single file from AI Studio.

    Supports both regular files and Git LFS objects
    (e.g. model checkpoints uploaded via ``ocean cloud upload``).

    Args:
        repo_id: ``username/repo-name``.
        path_in_repo: File path within the repo.
        local_dir: Local directory to save to.
        repo_type: ``"dataset"`` or ``"model"``.
        revision: Branch name.
        token: AI Studio access token. Falls back to stored token.

    Returns:
        Path to the downloaded file.

    Examples:
        >>> download_file("PlumBlossom/MyModel", "rmvpe.pdparams", repo_type="model")
    """
    token = token or get_token()
    _config.validate_repo_id(repo_id)
    dest_dir = Path(local_dir).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Get file info (checks if LFS)
    git_host = os.getenv("STUDIO_GIT_HOST", _config.GIT_HOST)
    url = f"{git_host}/api/v1/repos/{repo_id}/contents/{path_in_repo}?ref={revision}"
    resp = requests.get(url, headers=_header_fill(token), timeout=30)
    resp.raise_for_status()
    file_info = resp.json()

    out = str(dest_dir / Path(path_in_repo).name)
    _download_with_lfs_check(repo_id, file_info, out, token, revision)
    return out
