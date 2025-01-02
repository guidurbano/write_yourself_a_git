import os
import sys
import zlib
import hashlib
from guit.utils import repo_file, repo_find, object_find
from guit.classes import GitRepository, GitObject, GitBlob


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
