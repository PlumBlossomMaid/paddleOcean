"""ocean model — export and serve trained models."""

import click


@click.group()
def model():
    """Export, serve, and manage trained models."""


@model.command()
@click.option("--checkpoint", "-c", required=True, help="Path to checkpoint file.")
@click.option("--format", "-f", type=click.Choice(["onnx"]), default="onnx", help="Export format.")
@click.option("--output", "-o", default=None, help="Output path.")
@click.option("--model-class", type=str, default=None, help="Model class for inference-only layers.")
def export(checkpoint, format, output, model_class):
    """Export a trained model to ONNX or other formats.

    Example:

        ocean model export --checkpoint codec.ckpt --format onnx --output codec.onnx
    """
    try:
        import paddle
    except ImportError:
        click.echo("Error: paddle is not installed.", err=True)
        return

    if format == "onnx":
        if not output:
            output = checkpoint.rsplit(".", 1)[0] + ".onnx"

        # Load checkpoint
        state_dict = paddle.load(checkpoint)

        # Build inference model
        if model_class:
            module_path, class_name = model_class.rsplit(".", 1)
            import importlib
            module = importlib.import_module(module_path)
            model_cls = getattr(module, class_name)
            model_instance = model_cls()
            model_instance.set_state_dict(state_dict)
            model_instance.eval()

            # Export to ONNX
            dummy_input = paddle.randn([1, 1026, 128])
            paddle.onnx.export(model_instance, output, input_spec=[dummy_input])
            click.echo(f"✅ Model exported to {output}")
        else:
            click.echo("Error: --model-class is required for ONNX export.", err=True)


@model.command()
@click.option("--model", "-m", required=True, help="Path to ONNX model.")
@click.option("--port", "-p", default=8501, type=int, help="Serving port.")
def serve(model, port):
    """Serve a model via HTTP.

    Example:

        ocean model serve --model codec.onnx --port 8501
    """
    click.echo(f"🚧 Serving {model} on port {port} (coming soon)")
