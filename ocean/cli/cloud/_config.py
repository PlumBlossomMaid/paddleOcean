"""AI Studio cloud configuration constants."""

import click

# Gitea host
GIT_HOST = "https://git.aistudio.baidu.com"

# AI Studio model API prefix
MODEL_API_PREFIX = "https://aistudio.baidu.com"

# Pipeline (job) API endpoints
PIPELINE_CREATE_URL = "/paddlex/v3/pipelines/sdk/create"
PIPELINE_CREATE_CALLBACK_URL = "/paddlex/v3/pipelines/sdk/create/callback"
PIPELINE_BOSACL_URL = "/paddlex/v3/file/api/bosacl"
PIPELINE_QUERY_URL = "/paddlex/v3/pipelines/sdk/list"
PIPELINE_STOP_URL = "/paddlex/v3/pipelines/sdk/stop"


def validate_repo_id(repo_id: str) -> str:
    """Validate that repo_id is in ``username/repo-name`` format."""
    if "/" not in repo_id or len(repo_id.split("/")) != 2:
        raise click.ClickException(
            f"Invalid repo_id: '{repo_id}'. Expected format: 'username/repo-name'"
        )
    user, repo = repo_id.split("/")
    if not user.strip() or not repo.strip():
        raise click.ClickException(
            f"Invalid repo_id: '{repo_id}'. Both username and repo name must be non-empty."
        )
    return repo_id
