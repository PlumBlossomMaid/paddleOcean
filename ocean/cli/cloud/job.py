"""cloud job — submit/manage training jobs on AI Studio."""

import json
import os

import click
import requests

from ocean.cli.cloud import _config
from ocean.cli.cloud.auth import get_token


def _api_url(path: str) -> str:
    prefix = os.getenv(
        "STUDIO_MODEL_API_URL_PREFIX", _config.MODEL_API_PREFIX
    )
    return f"{prefix}{path}"


def _post(path: str, data: dict, token: str):
    resp = requests.post(
        _api_url(path),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"token {token}",
        },
        json=data,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


@click.group()
def job():
    """Manage AI Studio training jobs."""


@job.command()
@click.option("--name", "-n", required=True, help="Job name.")
@click.option("--cmd", "-c", required=True, help="Command to run.")
@click.option("--path", "-p", required=True, help="Local code path (directory, max 50MB).")
@click.option("--env", default="paddle2.6_py3.10", help="Environment.")
@click.option("--gpus", type=int, default=1, help="Number of GPUs.")
@click.option("--device", default="v100", help="Device type.")
@click.option("--token", default=None, help="AI Studio access token.")
def submit(name, cmd, path, env, gpus, device, token):
    """Submit a training job to AI Studio.

    Example:

        ocean cloud job submit \\
            --name codec-training \\
            --cmd "python train_codec.py --config codec.yaml" \\
            --path ./codec \\
            --gpus 4
    """
    token = token or get_token()

    # Package code (basic check)
    import tempfile
    import zipfile
    from pathlib import Path

    code_path = Path(path)
    if not code_path.is_dir():
        click.echo("Error: --path must be a directory.", err=True)
        return

    # Create zip
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        zip_path = tmp.name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in code_path.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                zf.write(f, f.relative_to(code_path))

    zip_size = Path(zip_path).stat().st_size
    if zip_size > 50 * 1024 * 1024:
        Path(zip_path).unlink()
        click.echo(f"Error: code package too large ({zip_size / 1024 / 1024:.1f} MB > 50 MB)", err=True)
        return

    try:
        resp = _post(
            _config.PIPELINE_CREATE_URL,
            {
                "name": name,
                "command": cmd,
                "env": env,
                "device": device,
                "gpus": gpus,
            },
            token,
        )
        click.echo(f"✅ Job submitted: {resp}")
    finally:
        Path(zip_path).unlink(missing_ok=True)


@job.command()
@click.argument("job_id", required=False, default=None)
@click.option("--name", "-n", default=None, help="Filter by job name.")
@click.option("--status", "-s", default=None, help="Filter by status.")
def list(job_id, name, status):
    """List or query training jobs."""
    token = get_token()
    params = {}
    if job_id:
        params["pipelineId"] = job_id
    if name:
        params["name"] = name
    if status:
        params["status"] = status

    resp = _post(_config.PIPELINE_QUERY_URL, params, token)
    click.echo(json.dumps(resp, indent=2, ensure_ascii=False))


@job.command()
@click.argument("job_id")
@click.option("--force", "-f", is_flag=True, help="Force stop without confirmation.")
def stop(job_id, force):
    """Stop a training job."""
    token = get_token()
    if not force:
        click.confirm(f"Stop job {job_id}?", abort=True)
    resp = _post(_config.PIPELINE_STOP_URL, {"pipelineId": job_id}, token)
    click.echo(f"✅ Job {job_id} stopped: {resp}")
