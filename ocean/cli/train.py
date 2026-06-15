"""ocean train — launch training from CLI."""

import importlib

import click

from ocean.trainer import Trainer


@click.command()
@click.option("--config", "-c", default=None, help="Path to YAML config file.")
@click.option(
    "--model",
    type=str,
    default=None,
    help="Fully qualified model class, e.g. 'my_module.MyModel'",
)
@click.option("--max-epochs", type=int, default=None, help="Max training epochs.")
@click.option("--max-steps", type=int, default=None, help="Max training steps.")
@click.option("--accelerator", type=str, default=None, help="Accelerator type.")
@click.option("--devices", type=str, default=None, help="Devices to use.")
@click.option("--precision", type=str, default=None, help="Precision mode.")
def train(config, model, max_epochs, max_steps, accelerator, devices, precision):
    """Start model training.

    Examples:

        ocean train --config codec.yaml

        ocean train --model my_model.CodecModel --max-epochs 100
    """
    # Build trainer from explicit params
    trainer_kwargs = {}
    if max_epochs is not None:
        trainer_kwargs["max_epochs"] = max_epochs
    if max_steps is not None:
        trainer_kwargs["max_steps"] = max_steps
    if accelerator is not None:
        trainer_kwargs["accelerator"] = accelerator
    if devices is not None:
        trainer_kwargs["devices"] = devices
    if precision is not None:
        trainer_kwargs["precision"] = precision

    # Import and build model
    model_instance = None
    if model:
        module_path, class_name = model.rsplit(".", 1)
        module = importlib.import_module(module_path)
        model_class = getattr(module, class_name)
        model_instance = model_class()

    if config:
        # Load YAML config and merge
        try:
            import yaml

            with open(config) as f:
                cfg = yaml.safe_load(f)
            for k, v in cfg.get("trainer", {}).items():
                if k not in trainer_kwargs or trainer_kwargs[k] is None:
                    trainer_kwargs[k] = v
        except ImportError:
            click.echo("Warning: pyyaml not installed, skipping config file.", err=True)
        except FileNotFoundError:
            click.echo(f"Error: config file {config} not found.", err=True)
            return

    trainer = Trainer(**trainer_kwargs)

    if model_instance is not None:
        trainer.fit(model_instance)
