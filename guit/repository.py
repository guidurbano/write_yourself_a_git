import os
import configparser

class GitRepository:
    """
    Represents a Git repository.

    Attributes:
        worktree (str): The working directory of the repository.
        gitdir (str): The directory containing Git metadata (e.g., `.git`).
        conf (ConfigParser): Configuration data loaded from the repository.

    """

    def __init__(self, path: str, force: bool = False):
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception(f"Not a Git repository {path}")

        # Read configuration file in .git/config
        self.conf = configparser.ConfigParser()
        cf = os.path.join(self.gitdir, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0: # only default repository format 0
                raise Exception(f"Unsupported repositoryformatversion {vers}")
