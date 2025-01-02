import argparse
import collections
import configparser

import os
import re
import sys
import zlib
from datetime import datetime

# import grp, pwd
from fnmatch import fnmatch
from math import ceil

from typer import Argument, Context, Typer, Option

from guit.create import repo_create
from guit.io import cat_file as _cat_file
from guit.io import object_hash

app = Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def default(ctx: Context):
    """Default action when no command is provided."""
    if not ctx.invoked_subcommand:
        print("Welcome to guit! Use --help for available commands.")


@app.command()
def init(
    path: str = Argument(default=".", metavar="directory", help="Path of repository.")
):
    """
    Initiate a new Git repository
    """

    repo_create(path)


@app.command()
def cat_file(
    type: str = Argument(
        default="blob", metavar="type", help="Specify the object type"
    ),
    object: str = Argument(metavar="object", help="The object to display"),
):
    """
    Provide content of repository objects.
    """
    if type not in ["blob", "commit", "tag", "tree"]:
        raise Exception(f"type should be either 'blob', 'commit', 'tag', 'tree'")
    _cat_file(type, object)


@app.command()
def hash_object(
    t: str = Option(default="blob", metavar="type", help="Specify the object type"),
    w: str = Option(
        default=False, is_flag=True, help="Actually write the object into the database"
    ),
    path: str = Argument(help="Read object from <file>"),
):
    """
    Provide content of repository objects.
    """
    if t not in ["blob", "commit", "tag", "tree"]:
        raise Exception(f"type should be either 'blob', 'commit', 'tag', 'tree'")
    object_hash(t, w, path)
