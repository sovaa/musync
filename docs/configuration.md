# Configuration

## Syntax

If you are familiar with the Python
[RawConfigParser](http://docs.python.org/lib/module-ConfigParser.html) you
should know already how keys and sections are defined. Musync has a few
quirks when it comes to parsing these, so it might be best to read on, even
though most things would seem quite familiar.

Configurations are read from `/etc/musync.conf` and `~/.musync` in that
respective order.

*The key that is defined last is the one used.*

Musync overwrites its configuration in *sections*. These act as *action*
references and tell musync how to behave. They are used with the `-c`
command-line option.

Sections look like the following:

```ini
[foo]
```

These are followed by a number of keys, which should look like the
following.

```ini
[general] # the general section is always loaded
root: /mnt/hdb1/music
coloring: true
[foo]
root: /mnt/hdc1/music
[bar]
coloring: false
```

## Keys

**root** --
Root directory where files will be handled into. Defaults to `None`.

**dir** --
This gives you a way to tell which directory the created files will have.

**format** --
This allows you to format the filename.

**lock-file** --
The file used for storing lock information in. Defaults to `None`.

**lock** --
Set to `true` or `false`, depending on if you want files to be locked after
an add or fix operation.

**default-config** --
The default configuration string used when the command-line option
`--config` (or `-c`) is not specified. This can handle linear references in
your configuration, but will fail if you try to configure it with circular
references (which could otherwise result in infinite loops). Defaults to
`None`.

**log** --
Where the log-file will be written, containing errors and such. Defaults to
`/tmp/musync.log`.

**fix-log** --
Where the fix-log will be written, containing names of files that need fixes
before they can be used with Musync. These are absolute paths, separated by
newlines (`\n`). Defaults to `/tmp/musync-fixes.log`.

**add-with** --
The command to run when adding files to the depository. Notice the Python
vars `%(source)s` and `%(dest)s`.

**rm-with** --
The command to run when removing files from the depository. Notice the
Python var `%(target)s`.

**filter-with** --
The command to clean metadata strings with. The Python variable `%(field)s`
is available to specify different files for different meta fields.

Example: `/usr/bin/sed -r -f /etc/musync.sed`

Or: `/usr/bin/sed -r -f /etc/musync.%(field)s.sed`

`%(field)s` will be expanded to either *artist*, *album* or *title*.

**hash-with** --
The command used to get the hash for a file. Output may be just the hash or
the hash with a space postfix containing anything.

**check-hash** --
Set to `true` or `false`, depending on if you want hash checking enabled or
not.

**coloring** --
Set to `true` or `false`, depending on if you want colored output or not.

**overwrite** --
If the file that is to be written already exists -- and this option is
`true` (which can be set with `-O` or `--overwrite` as well) -- all files
that already exist will be first removed with `rm-with` before adding the
file.

**no-fixme** --
Prevents fixme-actions from being taken. This might be necessary if you
really want to add broken files to your repository.
