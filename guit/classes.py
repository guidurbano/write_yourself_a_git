import configparser
import os

from guit.parser import kvlm_parse, kvlm_serialize


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
            if vers != 0:  # only default repository format 0
                raise Exception(f"Unsupported repositoryformatversion {vers}")


class GitObject:
    """
    Represents a Git object.
    Either loads the object from the provided data or create a new empty
    object.

    Attributes:

    """

    def __init__(self, data=None):
        if data != None:
            self.deserialize(data)
        else:
            self.init()

    def serialize(self, repo):
        """
        This function MUST be implemented by subclasses.
        It must read the object's contents from self.data, a byte string, and do
        whatever it takes to convert it into a meaningful representation.
        What exactly that means depend on each subclass.
        """
        raise Exception("Unimplemented!")

    def deserialize(self, data):
        raise Exception("Unimplemented!")

    def init(self):
        pass  # Just do nothing. This is a reasonable default!


class GitBlob(GitObject):
    """
    Basic blob object
    This is the type of object of every file in git.
    """

    fmt = b"blob"

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data


class GitCommit(GitObject):
    """
    Commit object.
    """

    fmt = b"commit"

    def deserialize(self, data):
        self.kvlm = kvlm_parse(data)

    def serialize(self):
        return kvlm_serialize(self.kvlm)

    def init(self):
        self.kvlm = dict()
