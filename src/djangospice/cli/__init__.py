import click # type: ignore
from .plugin import createplugin
from .plugin import plugin
from .system import system

@click.group()
def cli():
    """djangospice CLI"""
    pass

cli.add_command(createplugin)
cli.add_command(plugin)
cli.add_command(system)

if __name__ == "__main__":
    cli()
