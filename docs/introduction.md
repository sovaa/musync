# Introduction

## What is musync?

**The short explanation:**
Musync sorts your music, using the metadata acquired from the files
themselves, which exists in most popular music formats as of today.

**The slightly longer:**
Musync is a strict, highly customizable music organizer. If it doesn't
behave in a logical way -- it is probably a bug.

Musync will *never* modify your original music files, unless you configure
it to do so. It was created to utilise the tools that already exist in a
sane operating system, since they are well tested and provide the highest
performance in the safest possible way.

## Requirements

**Compulsory**

- [Python](http://python.org)
- [Mutagen](https://mutagen.readthedocs.io/) library for Python

**Recommended**

- \*nix Coreutils (`mv`, `cp`, `ln`, etc.)
- [GNU Sed](http://www.gnu.org/software/coreutils/)

## Installation

Run

```
> setup.py install
```

as superuser to install. By default musync will try to put all necessary
files in

```
/usr/share/musync
```

and it is up to the user to copy these into the right position.

Musync scans the following directories for configuration files:

- `/etc/musync.conf`
- `~/.musyncrc`
