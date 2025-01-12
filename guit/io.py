import hashlib
import os
import sys
import zlib

from guit.classes import GitBlob, GitCommit, GitObject, GitRepository
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


def object_hash(type: str, write: bool, path: str):
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
