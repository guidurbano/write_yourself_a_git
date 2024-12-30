import argparse
import collections
import configparser
import hashlib
import os
import re
import sys
import zlib
from datetime import datetime

# import grp, pwd
from fnmatch import fnmatch
from math import ceil

from typer import Argument, Context, Typer

from guit.create import repo_create

app = Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def default(ctx: Context):
    """Default action when no command is provided."""
    if not ctx.invoked_subcommand:
        print("Welcome to guit! Use --help for available commands.")


@app.command()
def init(
    path: str = Argument(
        default=".", metavar="directory", help="Initialize a new, empty repository."
    )
):
    """
    Initiate a new Git repository
    """

    repo_create(path)
