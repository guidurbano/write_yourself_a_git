import os

from guit.repository import GitRepository


def repo_path(repo, *path):
    """Compute path under repo's gitdir."""
    return os.path.join(repo.gitdir, *path)


def repo_file(repo: GitRepository, *path: str, mkdir: bool = False) -> str:
    """
    Generate a path for a file inside the Git directory.

    If `mkdir` is True, the parent directories of the file are created if they
    do not exist.

    Parameters:
        repo (GitRepository): The repository instance.
        path (str): Path components relative to the Git directory.
        mkdir (bool): Whether to create the parent directories if missing.

    Returns:
        str: The full path to the file.
    """
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return os.path.join(repo.gitdir, *path)


def repo_dir(repo: GitRepository, *path: str, mkdir: bool = False) -> str:
    """
    Generate a path for a directory inside the Git directory.

    If `mkdir` is True, the directory is created if it does not exist.

    Parameters:
        repo (GitRepository): The repository instance.
        path (str): Path components relative to the Git directory.
        mkdir (bool): Whether to create the directory if missing.

    Returns:
        str: The full path to the directory, or None if it does not exist.
    """

    dir_path = os.path.join(repo.gitdir, *path)

    if os.path.exists(dir_path):
        if os.path.isdir(dir_path):
            return dir_path
        raise Exception(f"Not a directory {dir_path}")

    if mkdir:
        os.makedirs(dir_path)
        return dir_path

    return None
