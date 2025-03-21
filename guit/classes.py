import configparser
import os


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


def kvlm_parse(raw, start=0, dct=None):
    """
    Parse function for Key-Value List with Message.

    Parameters:
        raw (bytes): The raw data to parse.
        start (int): The starting index in raw data.
        dct (dict): Dictionary to store parsed data.

     Returns:
         dict: Parsetd KVLM data.
    """
    if not dct:
        dct = dict()
        # You CANNOT declare the argument as dct=dict() or all call to
        # the functions will endlessly grow the same dict.

    # This function is recursive: it reads a key/value pair, then call
    # itself back with the new position.  So we first need to know
    # where we are: at a keyword, or already in the messageQ

    # We search for the next space and the next newline.
    spc = raw.find(b" ", start)
    nl = raw.find(b"\n", start)

    # If space appears before newline, we have a keyword.  Otherwise,
    # it's the final message, which we just read to the end of the file.

    # Base case
    # =========
    # If newline appears first (or there's no space at all, in which
    # case find returns -1), we assume a blank line.  A blank line
    # means the remainder of the data is the message.  We store it in
    # the dictionary, with None as the key, and return.
    if spc < 0 or (nl >= 0 and nl < spc):
        assert nl == start
        dct[None] = raw[start + 1 :]
        return dct

    # Recursive case
    # ==============
    # we read a key-value pair and recurse for the next.
    key = raw[start:spc]

    # Find the end of the value.  Continuation lines begin with a
    # space, so we loop until we find a "\n" not followed by a space.
    end = spc
    while True:
        end = raw.find(b"\n", end + 1)
        if raw[end + 1] != ord(" "):
            break

    # Grab the value
    # Also, drop the leading space on continuation lines
    value = raw[spc + 1 : end].replace(b"\n ", b"\n")

    # Don't overwrite existing data contents
    if key in dct:
        if type(dct[key]) == list:
            dct[key].append(value)
        else:
            dct[key] = [dct[key], value]
    else:
        dct[key] = value

    return kvlm_parse(raw, end + 1, dct)


def kvlm_serialize(kvlm):
    """
    Serialize KVLM data into raw bytes.

    Parameters:
        kvlm (dict): KVLM data to serialize.

    Returns:
        bytes: Serialized KVLM data.
    """
    ret = b""

    # Output fields
    for k in kvlm.keys():
        # Skip the message itself
        if k is None:
            continue
        val = kvlm[k]
        # Normalize list
        val = [val] if not isinstance(val, list) else val
        for v in val:
            ret += k + b" " + v.replace(b"\n", b"\n ") + b"\n"

    # Append message
    ret += b"\n" + kvlm[None]

    return ret


class GitTreeLeaf(object):
    """
    Leaf object from a tree.
    """

    def __init__(self, mode, path, sha):
        self.mode = mode
        self.path = path
        self.sha = sha


class GitTree(GitObject):
    """
    Tree object.
    """

    fmt = b"tree"

    def deserialize(self, data):
        self.items = tree_parse(data)

    def serialize(self):
        return tree_serialize(self)

    def init(self):
        self.items = list()


def tree_parse_one(raw, start=0):
    """
    Parse a single tree item from raw data.

    Parameters:
        raw (bytes): Raw tree data.
        start (int): Starting index.

    Returns:
        tuple: (Next index, GitTreeLeaf)
    """
    # Find the space terminator of the mode
    x = raw.find(b" ", start)
    assert 5 <= (x - start) <= 6

    # Read the mode
    mode = raw[start:x]
    # Normalize to six bytes.
    mode = b"0" + mode if len(mode) == 5 else mode

    # Find the NULL terminator of the path
    y = raw.find(b"\x00", x)
    # and read the path
    path = raw[x + 1 : y]

    # Read the SHA…
    raw_sha = int.from_bytes(raw[y + 1 : y + 21], "big")
    # and convert it into an hex string, padded to 40 chars
    # with zeros if needed.
    sha = format(raw_sha, "040x")
    return y + 21, GitTreeLeaf(mode, path.decode("utf8"), sha)


def tree_parse(raw):
    """
    Parse a Git tree object.

    Parameters:
        raw (bytes): Raw tree data.

    Returns:
        list: List of GitTreeLeaf objects.
    """
    pos = 0
    items = []
    while pos < len(raw):
        pos, leaf = tree_parse_one(raw, pos)
        items.append(leaf)
    return items


def tree_leaf_sort_key(leaf):
    """
    Sort key for tree leaves.

    Parameters:
        leaf (GitTreeLeaf): Tree leaf object.

    Returns:
        str: Sorting key.
    """
    return leaf.path if leaf.mode.startswith(b"10") else leaf.path + "/"


def tree_serialize(obj):
    """
    Serialize a Git tree object.

    Parameters:
        obj (GitTree): Tree object.

    Returns:
        bytes: Serialized tree data.
    """

    obj.items.sort(key=tree_leaf_sort_key)
    ret = b""
    for item in obj.items:
        ret += item.mode + b" " + item.path.encode("utf-8") + b"\x00"
        ret += int(item.sha, 16).to_bytes(20, "big")
    return ret


class GitTag(GitCommit):
    """
    Tag object (same structure as a commti with PGP signature, author
    date)
    """

    fmt = b"tag"


class GitIndexEntry(object):
    def __init__(
        self,
        ctime=None,
        mtime=None,
        dev=None,
        ino=None,
        mode_type=None,
        mode_perms=None,
        uid=None,
        gid=None,
        fsize=None,
        sha=None,
        flag_assume_valid=None,
        flag_stage=None,
        name=None,
    ):
        # The last time a file's metadata changed.  This is a pair
        # (timestamp in seconds, nanoseconds)
        self.ctime = ctime
        # The last time a file's data changed.  This is a pair
        # (timestamp in seconds, nanoseconds)
        self.mtime = mtime
        # The ID of device containing this file
        self.dev = dev
        # The file's inode number
        self.ino = ino
        # The object type, either b1000 (regular), b1010 (symlink),
        # b1110 (gitlink).
        self.mode_type = mode_type
        # The object permissions, an integer.
        self.mode_perms = mode_perms
        # User ID of owner
        self.uid = uid
        # Group ID of ownner
        self.gid = gid
        # Size of this object, in bytes
        self.fsize = fsize
        # The object's SHA
        self.sha = sha
        self.flag_assume_valid = flag_assume_valid
        self.flag_stage = flag_stage
        # Name of the object (full path this time!)
        self.name = name


class GitIndex(object):
    version = None
    entries = []
    # ext = None
    # sha = None

    def __init__(self, version=2, entries=None):
        if not entries:
            entries = list()

        self.version = version
        self.entries = entries
