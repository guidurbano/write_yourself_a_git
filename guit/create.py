import os
import configparser
from guit.repository import GitRepository
from guit.utils import repo_dir, repo_file

def repo_create(path: str) -> GitRepository:
    """
    Create a new Git repository at the specified path.

    This function initializes the repository by creating the necessary
    directories, configuration files, and default settings.

    Parameters:
        path (str): The file system path where the repository should be created.

    Returns:
        GitRepository: The newly created repository instance.

    Raises:
        Exception: If the target path is not a directory or is not empty.
    """

    repo = GitRepository(path, force=True)

    # First, we make sure the path either doesn't exist or is an
    # empty dir.

    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree) or (
            os.path.exists(repo.gitdir) and os.listdir(repo.gitdir)):
            raise Exception(f"{path} is not a valid or empty directory!")
    else:
        os.makedirs(repo.worktree)

    create_git_structure(repo)

    return repo

def create_git_structure(repo: GitRepository):
    """
    Create the directory and file structure for a Git repository.

    Parameters:
        repo (GitRepository): The repository instance.
    """
    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    with open(repo_file(repo, "description"), "w") as f:
        f.write("Unnamed repository; edit this file to name the repository.\n")

    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)


def repo_default_config() -> configparser.ConfigParser:
    """
    Generate the default configuration for a Git repository.

    Returns:
        ConfigParser: The default configuration settings.
    """
    ret = configparser.ConfigParser()

    ret.add_section("core")
    # version of gitdit format (0 is initial format)
    ret.set("core", "repositoryformatversion", "0")
    # disable tracking of file modes permissions changes in the work tree
    ret.set("core", "filemode", "false")
    # indicates this repository has a worktree
    ret.set("core", "bare", "false")

    return ret
