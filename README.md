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

#### what is a commit?


A commit object uncompressed without headers has this format:

- A tree object
- Zero, one or more parents;
- An author identity (name and email), and a timestamp;
- A committer identity (name and email), and a timestamp;
- An optional PGP signature
- A message

```bash
tree 29ff16c9c14e2652b22f8b78bb08a5a07930c147
parent 206941306e8a8af65b66eaaaea388a7ae24d49a0
author Thibault Polge <thibault@thb.lt> 1527025023 +0200
committer Thibault Polge <thibault@thb.lt> 1527025044 +0200
gpgsig -----BEGIN PGP SIGNATURE-----

 iQIzBAABCAAdFiEExwXquOM8bWb4Q2zVGxM2FxoLkGQFAlsEjZQACgkQGxM2FxoL
 kGQdcBAAqPP+ln4nGDd2gETXjvOpOxLzIMEw4A9gU6CzWzm+oB8mEIKyaH0UFIPh
 rNUZ1j7/ZGFNeBDtT55LPdPIQw4KKlcf6kC8MPWP3qSu3xHqx12C5zyai2duFZUU
 wqOt9iCFCscFQYqKs3xsHI+ncQb+PGjVZA8+jPw7nrPIkeSXQV2aZb1E68wa2YIL
 3eYgTUKz34cB6tAq9YwHnZpyPx8UJCZGkshpJmgtZ3mCbtQaO17LoihnqPn4UOMr
 V75R/7FjSuPLS8NaZF4wfi52btXMSxO/u7GuoJkzJscP3p4qtwe6Rl9dc1XC8P7k
 NIbGZ5Yg5cEPcfmhgXFOhQZkD0yxcJqBUcoFpnp2vu5XJl2E5I/quIyVxUXi6O6c
 /obspcvace4wy8uO0bdVhc4nJ+Rla4InVSJaUaBeiHTW8kReSFYyMmDCzLjGIu1q
 doU61OM3Zv1ptsLu3gUE6GU27iWYj2RWN3e3HE4Sbd89IFwLXNdSuM0ifDLZk7AQ
 WBhRhipCCgZhkj9g2NEk7jRVslti1NdN5zoQLaJNqSwO1MtxTmJ15Ksk3QP6kfLB
 Q52UWybBzpaP9HEd4XnR+HuQ4k2K0ns2KgNImsNvIyFwbpMUyUWLMPimaV1DWUXo
 5SBjDB/V/W2JBFR+XKHFJeFwYhj7DD/ocsGr4ZMx/lgc8rjIBkI=
 =lgTX
 -----END PGP SIGNATURE-----

Create first draft
```

All this hashed together in a unique SHA-1 identifier.

> Important to note that dictionaries preserve the insertion order and this
> is essential in Git since if we change the order (e.g. putting tree after
> parent), we'd modify the SHA-1 hash of the commit and this would be two
> equivalent but distinct commits.

Since commit is made out of it's parents, they are immutable and
have the hole history

## Contribution

Contributions are welcome! Feel free to fork the repository and submit a pull request.
