__author__ = 'J41R0'

import os
import click
import shutil
from pathlib import Path

from xintesis.template import default

CTX_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CTX_SETTINGS)
def xsa_cli():
    pass


@click.command()
@click.pass_context
def help(ctx):
    """Show this message and exit. Use <command> -h to see detailed help"""
    print(ctx.parent.get_help())


@click.command()
@click.argument('dir', required=True)
@click.option('-r', count=True, help='Remove all files if not empty folder')
def create_api(dir, r):
    """Create api structure in desired directory"""
    if r:
        if os.path.exists(dir):
            shutil.rmtree(dir)

    api_dir = Path(dir)
    api_dir.mkdir(parents=True, exist_ok=True)
    wdir = str(api_dir.absolute())
    Path(wdir + "/doc").mkdir(exist_ok=True)
    Path(wdir + "/modules").mkdir(exist_ok=True)
    Path(wdir + "/packages/demo/test").mkdir(parents=True, exist_ok=True)
    Path(wdir + "/projects/default_proj/test").mkdir(parents=True, exist_ok=True)
    Path(wdir + "/test").mkdir(exist_ok=True)

    default.create_defaults(wdir)

    print("New service API created in '" + wdir + "'")


xsa_cli.add_command(help)
xsa_cli.add_command(create_api)

if __name__ == '__main__':
    xsa_cli()
