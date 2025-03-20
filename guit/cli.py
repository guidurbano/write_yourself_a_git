from typer import Argument, Context, Option, Typer

from guit.create import repo_create
from guit.io import (
    cat_file as _cat_file,
    checkout as _checkout,
    hash_object as _hash_object,
    log_commit,
    ls_tree as _ls_tree,
    tag as _tag,
    rev_parse as _rev_parse,
)
from guit.ref import show_ref as _show_ref

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
    w: bool = Option(
        default=False, is_flag=True, help="Actually write the object into the database"
    ),
    path: str = Argument(help="Read object from <file>"),
):
    """
    Hash an object.
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
    r: bool = Option(default=False, is_flag=True, help="Recurse into sub-trees"),
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
    Checkout a commit inside of a directory.
    """
    _checkout(commit, path)


@app.command()
def show_refs(
    with_hash: bool = Option(default=False, is_flag=True, help="Show hash."),
):
    """
    List references.
    """
    _show_ref(with_hash=with_hash, prefix="refs")


@app.command()
def tag(
    a: bool = Option(
        default=False, is_flag=True, help="Whether to create a tag object."
    ),
    name: str = Option(default=None, help="The new tag's name."),
    object: str = Option(default="HEAD", help="The object the new tag will point to."),
):
    """
    List and create tags.
    """
    _tag(annotate=a, name=name, object=object)


@app.command()
def rev_parse(
    guit_type: str = Option(
        default=None, metavar="type", help="Specify the expected type."
    ),
    name: str = Argument(help="The name to parse."),
):
    """
    Parse revision (or other objects) identifiers.
    """
    if guit_type not in ["blob", "commit", "tag", "tree"]:
        raise Exception(f"type should be either 'blob', 'commit', 'tag', 'tree'")

    _rev_parse(guit_type=guit_type, name=name)
