# Write yourself a Git

Implementation of the Git from scratch.
To understand the fundamentals of Git, the CLI tool was developed using Python
and basic shell. The idea comes from [Thibault Polge article](https://wyag.thb.lt/#intro).

The entire application is based on a `guit` command (git with an "extra u").

## How to use it

A very simplified version of Git core commands was implemented.
The list of commands are displayed with command `guit --help`.

### 1. Creating repositories: init

To initialize a new, empty repository:
``` bash
guit init [path]
```
This function initializes the repository by creating the necessary
directories and configuration files:.

``` bash
.git
│───config: configuration file (repositoryformatversion, filemode, bare)
│───description: free-form description of repository (rarely used)
│───HEAD: the reference to the current HEAD (e.g. refs/heads/master)
│
├───branches
├───objects: the object store
└───refs: the reference store
    ├───heads
    └───tags
```

The `config` file is set to:

``` bash
[core]
# the version of the gitdir format.
# 0 means the initial format, 1 the same with extensions.
# guit will only accept 0.
repositoryformatversion = 0
# disable tracking of file modes (permissions) changes in the work tree.
filemode = false
# indicates that this repository has a worktree.
# guit does not support optional worktree key
bare = false
```

### 2. Reading and writing objects

Two commands are implemented: `cat-file`and `hash-object`. There are not
very known... but they are quite simple. The `hash-object` converts
a file to a git object, and `cat-file` prints the raw content of an object,
uncompressed and without the git header.

If you are very confused about Git objects, read a basic understanding of [Git objects](#git-objects "Goto Git-objects").

For example, if you use:

```bash
guit cat-file blob d110cf2ee6b39b1224e6919d26aac168533289d7
```

You will see the contents of the first version of README.


To write a file, you use:

```bash
guit hash-file blob -w README.md
```

The parameter `-w` is used to actually write the object into the git repository.

## To know more

### Git-objects

#### why is this important?

Git is a **“content-addressed filesystem”** - which means the name of a file
is derived mathematically from the contents it has.

This implies in every modification in a file in git means creating a new file in a different path.

The path where git stores a given object is computed by calculating the SHA-1 hash of its contents.

#### the path

The mathematical computation is done by a hash function, which is a kind of unidirectional mathematical function: it is easy to compute the hash of a value, but there’s no way to compute back which value produced a hash.

Git renders the hash as a lowercase hexadecimal string, and splits it in two parts: the first two characters, and the rest. It uses the first part as a directory name, the rest as the file name:

The object with SHA-1 equals to `d110cf2ee6b39b1224e6919d26aac168533289d7` is store in `.git/objects/d1/10cf2ee6b39b1224e6919d26aac168533289d7`.

Git’s method creates 256 possible intermediate directories, hence dividing the average number of files per directory by 256

#### format

An object starts with a header that specifies its type: blob, commit, tag or tree (blobs have no actual format, the most simplest of them).

This header is followed by an ASCII space (0x20), then the size of the object in bytes as an ASCII number, then null (0x00) (the null byte), then the contents of the object.

> header + ' ' + str(len(data)).encode() + b'\x00' + data

Writing an object is reading it in reverse: we compute the hash of the object after
inserting the header, zlib compress everything and write to the location.

## Contribution

Contributions are welcome! Feel free to fork the repository and submit a pull request.
