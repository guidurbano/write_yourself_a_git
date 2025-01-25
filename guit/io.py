import hashlib
import os
import sys
import zlib

from guit.classes import GitBlob, GitCommit, GitObject, GitRepository, GitTree
from guit.utils import object_find, repo_file, repo_find


def object_read(repo: GitRepository, sha: str) -> GitObject:
    """Read object sha from Git repository repo.
    There are four object types: blob, commit, tag, tree

    Parameters:
        repo: Git repository of object
        sha (str): SHA-1 hash of object
    Return:
        GitObject whose exact type depends on the object.
    """

    # path is composed of first two characters + "/" + remaining sha
    # e673d1b7eaa0aa01b5bc2442d570a765bdaae751 path is:
    # .git/objects/e6/73d1b7eaa0aa01b5bc2442d570a765bdaae751
    path = repo_file(repo, "objects", sha[0:2], sha[2:])

    if not os.path.isfile(path):
        return None

    with open(path, "rb") as f:  # read file as binary
        raw = zlib.decompress(f.read())

        # Read object type
        x = raw.find(b" ")
        fmt = raw[0:x]

        # Read and validate object size
        y = raw.find(b"\x00", x)
        size = int(raw[x:y].decode("ascii"))
        if size != len(raw) - y - 1:
            raise Exception(f"Malformed object {sha}: bad length")

        # Pick constructor for that object format
        match fmt:
            case b"commit":
                c = GitCommit
            case b"tree":
                c = GitTree
            case b"tag":
                c = GitTag
            case b"blob":
                c = GitBlob
            case _:
                raise Exception(f"Unknown type {fmt.decode("ascii")} for object {sha}")

        # Call constructor and return object
        return c(raw[y + 1 :])


def object_write(obj: GitObject, repo=None):
    """
    Write a GitObject.
    Compute the hash, insert the header, compress with zlib and write.
    Parameters:
        obj: object
        repo: repository. Default is none.
    """
    # Serialize object data
    data = obj.serialize()
    # Add header
    ## Exact storage format is:
    ## header + space + size in bytes + null byte + contents
    result = obj.fmt + b" " + str(len(data)).encode() + b"\x00" + data
    # Compute hash
    sha = hashlib.sha1(result).hexdigest()

    if repo:
        # Compute path
        path = repo_file(repo, "objects", sha[0:2], sha[2:], mkdir=True)

        if not os.path.exists(path):
            with open(path, "wb") as f:
                # Compress and write
                f.write(zlib.compress(result))
    return sha


def cat_file(type: str, object: str):
    """
    Provide content of repository objects.
    Parameters:
        type (str): object type
        object (str): object name
    """
    repo = repo_find()
    obj = object_read(repo, object_find(repo, object, type.encode()))
    sys.stdout.buffer.write(obj.serialize())


def hash_object(type: str, write: bool, path: str):
    """
    Hash object, writing it to repo if provided.
    Parameters:
        type (str): object type
        write (str): actually write the object into database
        path (str): path
    """
    if write:
        repo = repo_find()
    else:
        repo = None

    with open(path, "rb") as fd:
        data = fd.read()

    fmt = type.encode()

    # Choose constructor according to fmt argument
    match fmt:
        case b"commit":
            obj = GitCommit(data)
        case b"tree":
            obj = GitTree(data)
        case b"tag":
            obj = GitTag(data)
        case b"blob":
            obj = GitBlob(data)
        case _:
            raise Exception(f"Unknown type {fmt}.")

    sha = object_write(obj, repo)
    print(sha)


def log_commit(commit: str):
    """
    Log that display history of a commit.

    Parameters:
        commit (str): commit sha-1 hash
    """
    repo = repo_find()
    print("```mermaid")
    print("graph TD")
    log_mermaid(repo, object_find(repo, commit), set())
    print("```")


def log_mermaid(repo, sha, seen):
    """
    Recursively generate Mermaid graph nodes and edges for a commit.

    Parameters:
        repo (GitRepository): Repository object.
        sha (str): SHA-1 hash of the commit.
        seen (set): Set of already processed commits to avoid duplication.
    """

    if sha in seen:
        return
    seen.add(sha)

    commit = object_read(repo, sha)
    message = commit.kvlm[None].decode("utf8").strip()
    message = message.replace("\\", "\\\\").replace('"', '\\"')

    # Display only the first line of the commit message
    if "\n" in message:
        message = message.split("\n")[0]

    print(f'  c_{sha}["{sha[:7]}: {message}"]')
    assert commit.fmt == b"commit"

    # Base case: the initial commit
    if b"parent" not in commit.kvlm:
        return

    parents = commit.kvlm[b"parent"]
    if not isinstance(parents, list):
        parents = [parents]

    for parent in parents:
        parent_sha = parent.decode("ascii")
        print(f"  c_{sha} --> c_{parent_sha}")
        log_mermaid(repo, parent_sha, seen)


def ls_tree(tree, recursive, prefix=""):
    """
    List the contents of a tree object.

    Parameters:
        tree (str): tree object.
        recursive (bool): Print the contests of a directory. Default if False.
        prefix (str): path prefix for recursive listings.
    """
    repo = repo_find()
    sha = object_find(repo, tree, fmt=b"tree")
    obj = object_read(repo, sha)
    print(obj)

    for item in obj.items:
        type = item.mode[:2] if len(item.mode) > 4 else item.mode[:1]
        type_map = {b"04": "tree", b"10": "blob", b"12": "blob", b"16": "commit"}
        type = type_map.get(type, None)

        if not type:
            raise Exception(f"Unknown tree leaf mode {item.mode}")

        full_path = os.path.join(prefix, item.path)

        if not (recursive and type == "tree"):
            mode_str = item.mode.decode("ascii").rjust(6, "0")
            print(f"{mode_str} {type} {item.sha}\t{full_path}")
        else:
            ls_tree(item.sha, recursive, full_path)


def checkout(commit, path):
    """
    Checkout a commit inside of a directory.

    Parameters:
        commit (str): Commit hash or tree to checkout.
        path (str): Directory where the commit should be checked out.
    """
    repo = repo_find()
    obj = object_read(repo, object_find(repo, commit))

    # If the object is a commit, we grab its tree
    if obj.fmt == b"commit":
        tree_sha = obj.kvlm[b"tree"].decode("ascii")
        obj = object_read(repo, tree_sha)

    # Ensure the target path is an empty directory
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise Exception(f"Path exists and is not a directory: {path}")
        if os.listdir(path):
            raise Exception(f"Directory is not empty: {path}")
    else:
        os.makedirs(path)

    tree_checkout(repo, obj, os.path.realpath(path))


def tree_checkout(repo, tree, path):
    """
    Recursively checkout a tree object.

    Parameters:
        repo: Repository instance.
        tree: Tree object to checkout.
        path (str): Directory path to populate with tree contents.
    """
    for item in tree.items:
        dest = os.path.join(path, item.path)
        obj = object_read(repo, item.sha)

        if obj.fmt == b"tree":
            os.makedirs(dest, exist_ok=True)
            tree_checkout(repo, obj, dest)
        elif obj.fmt == b"blob":
            with open(dest, "wb") as f:
                f.write(obj.blobdata)
