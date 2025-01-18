import os
from guit.utils import repo_dir, repo_file, repo_find


def ref_resolve(repo, ref):
    """
    Returns sha-1 identifier from a references or recursive references
    (the ones that begin with ref:)
    """
    path = repo_file(repo, ref)

    # Sometimes, an indirect reference may be broken.  This is normal
    # in one specific case: we're looking for HEAD on a new repository
    # with no commits.  In that case, .git/HEAD points to "ref:
    # refs/heads/main", but .git/refs/heads/main doesn't exist yet
    # (since there's no commit for it to refer to).
    if not os.path.isfile(path):
        return None

    with open(path, 'r') as fp:
        data = fp.read()[:-1]
        # Drop final \n ^^^^^
    if data.startswith("ref: "):
        return ref_resolve(repo, data[5:])
    else:
        return data


def ref_list(repo, path=None):
    """
    Simply list all references in .refs/
    """
    if not path:
        path = repo_dir(repo, "refs")
    ret = dict()
    # Git shows refs sorted.  To do the same, we sort the output of
    # listdir
    for f in sorted(os.listdir(path)):
        can = os.path.join(path, f)
        if os.path.isdir(can):
            ret[f] = ref_list(repo, can)
        else:
            ret[f] = ref_resolve(repo, can)

    return ret

def show_ref(repo=None, refs=None, with_hash=True, prefix=""):
    """
    List references.
    """
    if repo is None:
        repo = repo_find()
    if refs is None:
        refs = ref_list(repo)

    for name, value in refs.items():
        full_name = f"{prefix}/{name}" if prefix else name
        if isinstance(value, dict):
            # Recursive case for nested references
            show_ref(repo=repo, refs=value, with_hash=with_hash, prefix=full_name)
        else:
            print(f"{value} {full_name}" if with_hash else full_name)
