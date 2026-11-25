import click
import subprocess
import sys
from .helpers import find_project_root


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
    name="system"
)
@click.pass_context
def system(ctx):
    """
    Passthrough to Django's `manage.py` with auto project root detection.
    """
    project_root = find_project_root()
    if project_root is None:
        click.echo("Error: No `manage.py` file found in this directory or any parent directories.", err=True)
        sys.exit(1)

    manage_path = project_root / "manage.py"

    if not manage_path.is_file():
        click.echo(f"Error: `manage.py` exists but is not a file: {manage_path}", err=True)
        sys.exit(1)

    # Use subprocess.run for better control and error handling
    try:
        command = [sys.executable, str(manage_path)] + ctx.args
        subprocess.run(command, check=True)
    except FileNotFoundError:
        click.echo(f"Error: Python executable not found at {sys.executable}", err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}", err=True)
        sys.exit(e.returncode)

