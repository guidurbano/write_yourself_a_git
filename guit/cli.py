from typer import Argument, Context, Option, Typer

from guit.create import repo_create
from guit.io import cat_file as _cat_file
from guit.io import checkout as _checkout
from guit.io import hash_object as _hash_object
from guit.io import log_commit
from guit.io import ls_tree as _ls_tree

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
    _hash_object(t, w, path)


@app.command()
def log(commit: str = Argument(default="HEAD", help="Commit to start at.")):
    """
    Display history of a given commit.
    """
    log_commit(commit)


@app.command()
def ls_tree(
    tree: str = Argument(default="HEAD", help="A tree-ish object."),
    r: str = Option(default=False, is_flag=True, help="Recurse into sub-trees"),
):
    """
    List the contents of a tree object.
    """
    _ls_tree(tree, r)


@app.command()
def checkout(
    commit: str = Argument(help="The commit or tree to checkout."),
    path: str = Argument(help="The EMPTY directory to checkout on."),
):
    """
    Checkout a commit inside of a directory
    """
    _checkout(commit, path)
