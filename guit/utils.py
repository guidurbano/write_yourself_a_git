import os
from guit.classes import GitRepository


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


def repo_find(path: str = ".", required: bool = True) -> GitRepository | None:
    """
    Recursive search for a `.git` directory starting from the given path
    and traversing upward.

    Parameters:
        path (str): Starting directory for the search. Defaults is current.
        required (bool): To raise exception if not found.

    Returns:
        GitRepository: The repository object if found.
        None: If no `.git` directory is found and `required` is False.
    """
    # Normalize the path to an absolute path
    path = os.path.realpath(path)

    # Check if the `.git` directory exists at this level
    if os.path.isdir(os.path.join(path, ".git")):
        return GitRepository(path)

    # Move to the parent directory
    parent = os.path.realpath(os.path.join(path, ".."))

    # If we've reached the root directory, handle the base case
    if parent == path:
        if required:
            raise Exception("No .git directory found in any parent directory.")
        return None

    # Recursively search in the parent directory
    return repo_find(parent, required)
