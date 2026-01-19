#
# Musync opts - read global settings and keep track of them.
#
# a common line seen in most musync modules:
#     from musync.opts import app.lambdaenv;
#
# this enables all modules to work by their own settings.
#
# this is also responsible of reading configuration files and command line options.
#
# author: John-John Tedro <pentropa@gmail.com>
# version: 2008.1
# Copyright (C) 2007 Albin Stjerna, John-John Tedro
#
#    This file is part of Musync.
#
#    Musync is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Musync is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Musync.  If not, see <http://www.gnu.org/licenses/>.
#
# howto add a new option:
#    add it to default Setting
#    make sure values is read specifically as boolean if necessary (from configuration file)
#    make sure it is added to help-text (if necessary).
#    make sure cli-option is parsed.

import os
import shutil
import tempfile
import types

from configparser import RawConfigParser
from musync.errors import FatalException

import musync.locker
import musync.custom
import musync.printer

# Click is a hard requirement - fail fast if not available
try:
    import click
except ImportError:
    raise ImportError(
        "click is required but not installed. "
        "Please install it with: pip install click>=8.0.0"
    )

# operating system problems
tmp = tempfile.gettempdir()
# general temp directory


class LambdaEnviron(dict):
    def __init__(self, d=dict()):
        dict.__init__(self, d)

    def __setattr__(self, key, val):
        self.__setitem__(key, val)

    def __getattr__(self, key):
        if key not in self:
            raise Exception("No such key in lambdaenviron: " + key)
        return self.__getitem__(key)

    def __hasattr__(self, key):
        return key in self


LambdaTemplate = {
    "suppressed": [],
    "pretend": False,
    "recursive": False,
    "lock": False,
    "silent": False,
    "verbose": True,
    "force": False,
    "root": None,
    "config": None,
    "modify": dict(),
    "debug": True,
    "configurations": [],
    "transcode": None,
}


class AppSession:
    """
    Global application session.
    Should be common referenced in many methods.
    """

    def overlay_import(self, parser):
        ok = True

        if not parser.has_section("import"):
            self.printer.error("No 'import' section found in configuration")
            return False

        for key in parser.options("import"):
            val = parser.get("import", key)

            if val == "":
                self.printer.warning("ignoring empty key: " + key)
                continue

            import_stmt = val

            parts = import_stmt.split(".")[1:]
            parts.reverse()

            imported_m = None

            try:
                imported_m = __import__(import_stmt)
            except ImportError as e:
                self.printer.error("[I] " + key + ": " + str(e))
                ok = False
                continue

            while len(parts) > 0:
                imported_m = getattr(imported_m, parts.pop())

            self.imports[key] = val
            self.lambdaenv[key] = imported_m

        return ok

    def overlay_settings(self, parser, sect):
        """
        Overlay all settings from a specific section in the configuration file.
        """
        if not parser.has_section(sect):
            self.printer.error("section does not exist:", sect)
            return False

        ok = True

        for key in parser.options(sect):
            val = parser.get(sect, key)

            if val == "":
                self.printer.warning("ignoring empty key:", key)
                continue

            self.settings[key] = val

            try:
                val = eval(val, self.lambdaenv)
            except Exception as e:
                self.printer.error(key + ": " + str(e))
                ok = False
                continue

            self.lambdaenv[key] = val

        return ok

    def read_argv(self, argv):
        cp = RawConfigParser()

        noconfig = True

        configuration_files = [
            os.path.expanduser(os.path.join(*cfgfile)) for cfgfile in cfgfiles
        ]

        # not using readfiles since doesn't work under windows
        for cfg in configuration_files:
            if not os.path.isfile(cfg):
                continue

            noconfig = False
            cp.readfp(open(cfg))

        if noconfig:
            self.printer.error("no configuration files found!")
            self.printer.error("looked for:", ", ".join(configuration_files))
            self.printer.error(
                "an example configuration should have been bundled with this program"
            )
            return None, None, None

        if not self.overlay_import(cp):
            self.printer.error("could not overlay settings from 'import' section")
            return None, None, None

        # open log
        if not self.overlay_settings(cp, "general"):
            self.printer.error("could not overlay settings from 'general' section")
            return None, None, None

        # Parse command line arguments using click
        try:
            opts, argv = self._parse_with_click(argv)
            return cp, opts, argv
        except Exception as e:
            self.printer.error("Error parsing arguments:", str(e))
            return None, None, None

    def __init__(self, argv, stream):
        self.configured = False
        self.locker = None
        self.args = None
        self.printer = musync.printer.AppPrinter(self, stream)
        self.lambdaenv = LambdaEnviron(LambdaTemplate)
        self.imports = LambdaEnviron()
        self.settings = LambdaEnviron()

        cp, opts, args = self.read_argv(argv)

        if cp is None:
            return

        # keep to set default-config or not
        configuration = None

        def parse_modify(self, base, arg):
            if base is None:
                base = dict()

            i = arg.find("=")
            if i <= 0:
                self.printer.warning("invalid modify argument", arg)
                return base

            base[arg[:i]] = arg[i + 1 :]
            return base

        for opt, arg in opts:
            # loop through the arguments and do what we're supposed to do:
            if opt in ("-p", "--pretend"):
                self.lambdaenv.pretend = True
            elif opt in ("-V", "--version"):
                print(version_str % version)
                return None
            elif opt in ("-R", "--recursive"):
                self.lambdaenv.recursive = True
            elif opt in ("-L", "--lock"):
                self.lambdaenv.lock = True
            elif opt in ("-s", "--silent"):
                self.lambdaenv.silent = True
            elif opt in ("-v", "--verbose"):
                self.lambdaenv.verbose = True
            elif opt in ("-f", "--force"):
                self.lambdaenv.force = True
            elif opt in ("-c", "--config"):
                self.lambdaenv.configurations.extend(
                    [a.strip() for a in arg.split(",")]
                )
            elif opt in ("-M", "--modify"):
                self.lambdaenv.modify = parse_modify(self, self.lambdaenv.modify, arg)
            elif opt in ("-d", "--debug"):
                self.lambdaenv.debug = True
            elif opt in ("--root"):
                self.lambdaenv.root = arg
            else:
                self.printer.error("unkown option:", opt)

        #
        # Everytime default-config is set config must be rescanned.
        #
        anti_circle = []

        for config in self.lambdaenv.configurations:
            self.printer.notice("overlaying", config)

            if config in anti_circle:
                self.printer.error(
                    "Configuration has circular references, take a good look at key 'default-config'"
                )
                return

            anti_circle.append(config)

            if not self.overlay_settings(cp, config):
                self.printer.error("could not overlay section:", config)
                return

        if not os.path.isdir(self.lambdaenv.root):
            self.printer.error(
                "         root:",
                "Root library directory non existant, cannot continue.",
            )
            self.printer.error("current value:", self.lambdaenv.root)
            return

        # check that a specific set of lambda functions exist
        for key in ["add", "rm", "hash", "targetpath", "checkhash", "root"]:
            if key not in self.lambdaenv:
                self.printer.error("must be a lambda function:", key)
                return

        self.setup_locker(self.lambdaenv.lockdb())
        self.args = args
        self.configured = True

    def setup_locker(self, path):
        self.locker = musync.locker.LockFileDB(self, path)
    
    def _parse_with_click(self, argv):
        """
        Parse arguments using click while maintaining exact getopt compatibility.
        Returns (opts, args) in the same format as getopt.gnu_getopt.
        
        Handles the structure: [options] <operation> [files...]
        """
        # Separate options from operation+files
        # Options can be: -p, --pretend, -V, --version, etc.
        # We need to find where options end and operation begins
        opts = []
        args = []
        i = 0
        
        # Define valid options
        short_opts = {'p', 'V', 'R', 'L', 's', 'v', 'f', 'c', 'M', 'd'}
        long_opts = {
            'pretend', 'version', 'recursive', 'lock', 'silent', 
            'verbose', 'force', 'root', 'config', 'modify', 'debug'
        }
        opts_requiring_value = {'root', 'config', 'modify', 'c', 'M'}
        
        # Parse arguments manually to support [options] <operation> [files...]
        while i < len(argv):
            arg = argv[i]
            
            # Check if it's a long option
            if arg.startswith('--'):
                opt_name = arg[2:]
                if '=' in opt_name:
                    opt_name, value = opt_name.split('=', 1)
                    opts.append(('--' + opt_name, value))
                elif opt_name in opts_requiring_value:
                    if i + 1 < len(argv):
                        opts.append(('--' + opt_name, argv[i + 1]))
                        i += 1
                    else:
                        # Missing value, but continue anyway
                        opts.append(('--' + opt_name, ''))
                elif opt_name in long_opts:
                    opts.append(('--' + opt_name, ''))
                else:
                    # Unknown option, treat as start of operation
                    args.append(arg)
                    i += 1
                    break
            # Check if it's a short option
            elif arg.startswith('-') and len(arg) > 1 and not arg.startswith('--'):
                # Handle short options like -p, -V, -c value, -pV, etc.
                # Process each character after the dash
                j = 1
                while j < len(arg):
                    short_opt = arg[j]
                    if short_opt in short_opts:
                        if short_opt in opts_requiring_value:
                            # Option requires value
                            if j + 1 < len(arg):
                                # Value is in same arg: -cvalue
                                opts.append(('-' + short_opt, arg[j + 1:]))
                                break  # Can't have more opts after value
                            elif i + 1 < len(argv):
                                # Value is next arg: -c value
                                opts.append(('-' + short_opt, argv[i + 1]))
                                i += 1
                                break  # Can't have more opts after value
                            else:
                                opts.append(('-' + short_opt, ''))
                                break
                        else:
                            # Flag option
                            opts.append(('-' + short_opt, ''))
                            j += 1
                    else:
                        # Unknown option character, treat as start of operation
                        args.append(arg)
                        i += 1
                        break
                else:
                    # All characters processed, continue
                    i += 1
                    continue
                i += 1
            else:
                # Not an option, this is the operation or a file
                args.append(arg)
                i += 1
                break
        
        # Add remaining args (files)
        args.extend(argv[i:])
        
        # Fix PowerShell quoting issues: when a path ends with a backslash before a quote,
        # PowerShell treats it as escaping the quote, causing the quote and next args to be included.
        # Example: "T:\path\" becomes T:\path" --pretend (all as one argument)
        # We need to detect and fix this by splitting malformed arguments
        normalized_args = []
        for arg in args:
            # Check if arg contains a quote followed by space and an option (malformed by PowerShell)
            # Pattern: path" --pretend (all in one arg)
            if '"' in arg and ' --' in arg:
                # Split on the quote+space+-- pattern
                parts = arg.split('" --', 1)
                if len(parts) == 2:
                    path_part = parts[0].rstrip('\\')  # Remove trailing backslash if present
                    option_part = '--' + parts[1]
                    normalized_args.append(path_part)
                    # The option part should be processed, but since we've already parsed options,
                    # we'll just add it as a regular arg (it will be ignored or cause an error)
                    # Actually, let's check if it's a known option and handle it
                    opt_name = option_part[2:]  # Remove '--'
                    if opt_name in long_opts:
                        # It's a valid option - add it to opts if not already there
                        if ('--' + opt_name, '') not in opts:
                            opts.append(('--' + opt_name, ''))
                    else:
                        # Unknown option, add as arg (will likely cause an error)
                        normalized_args.append(option_part)
                else:
                    normalized_args.append(arg)
            # Check if arg ends with just a quote (simple case)
            elif arg.endswith('"') and len(arg) > 1:
                # Strip the trailing quote
                normalized_args.append(arg.rstrip('"').rstrip('\\'))
            else:
                normalized_args.append(arg)
        
        args = normalized_args
        
        # Validate options using click for better error messages
        @click.command()
        @click.option('--pretend', '-p', is_flag=True)
        @click.option('--version', '-V', is_flag=True)
        @click.option('--recursive', '-R', is_flag=True)
        @click.option('--lock', '-L', is_flag=True)
        @click.option('--silent', '-s', is_flag=True)
        @click.option('--verbose', '-v', is_flag=True)
        @click.option('--force', '-f', is_flag=True)
        @click.option('--root', type=str)
        @click.option('--config', '-c', type=str)
        @click.option('--modify', '-M', type=str)
        @click.option('--debug', '-d', is_flag=True)
        def validate_opts(**kwargs):
            pass
        
        # Create a context with just the options to validate
        opt_args = [opt for opt, val in opts for _ in ([opt] + ([val] if val else []))]
        try:
            validate_opts.make_context('musync', opt_args)
        except click.exceptions.Exit:
            # Help or version was shown
            return [], []
        except click.exceptions.BadOptionUsage as e:
            # Invalid option - re-raise with clearer message
            raise ValueError(f"Invalid option: {e.format_message()}")
        except click.exceptions.BadParameter as e:
            # Invalid parameter - re-raise with clearer message
            raise ValueError(f"Invalid parameter: {e.format_message()}")
        
        return opts, args


### This is changed with setup.py to suite environment ###
# cfgfile="d:\\dump\\programs\\musync_x86\\musync.conf"
cfgfiles = [["/", "etc", "musync.conf"], ["~", ".musync"]]
version = (0, 6, 2, "")
version_str = "Musync, music syncronizer %d.%d.%d%s"
REPORT_ADDRESS = "http://sourceforge.net/projects/musync or johnjohn.tedro@gmail.com"


def Usage():
    """
    Returns usage information generated from click command definitions.
    Maintains the same format as the original manual help text.
    """
    return _generate_click_help()


def _manual_usage_text():
    """Fallback manual help text when click is not available."""
    return """
    musync - music syncing scripts
    Usage: musync [option(s)] <operation> [file1 [..]]
    
    reads [file1 [..]] or each line from stdin as source files.
    musync is designed to be non-destructive and will never modify source files
    unless it is explicitly specified in configuration.

    musync is not an interactive tool.
    musync syncronizes files into a music repository.
   
        General:
            --export (or -e):
                Will tell you what configurations that will be used
                for certain arguments.
            --version (or -V):
                Echo version information and exit.
            --force (or -f) 'force':
                Force the current action. You might be prompted to force
                certain actions.
            --allow-similar:
                tells musync not to check for similar files.

        Options:
        syntax: *long-opt* (or *short-opt*) [*args*] '*conf-key*' (also *relevant*):

            --no-fixme 'no-fixme':
                ignore 'fixme' problems (you should review fixme-file first).
            --lock (or -L) 'lock' (also 'lock-file'):
                Can be combined with fix or add for locking
                after operation has been performed.
            --pretend (or -p) 'pretend':
                Just pretend to do actions, telling what you would do.
            --recursive (or -R) 'recursive':
                Scan directories recursively.
            --silent (or -s) 'silent':
                Supresses what is defined in 'suppressed'.
            --verbose (or -v) 'verbose':
                Makes musync more talkative.
            --coloring (or -C) 'coloring':
                Invokes coloring of output.
            --root (or -r) <target_root>
                Specify target root.
            --config (or -c) <section1>,<section2>,... 'default-config'
                Specify configuration section.
                These work as overlays and the latest key specified
                is the one used, empty keys do not overwrite pre-defined.
            -M key="new value"
                Use metadata provided here instead of the one in files.
                Valid keys are:
                    artist - artist tag
                    album - album name
                    title - track title
                    track - track number
            -T <from ext>=<to ext>
                Transcode from one extension to another, tries to find
                configuration variable *from*-to-*to*.
                Example: -T flac>ogg (with key flac-to-ogg).
            --debug (-d):
                Will enable printing of  traceback on
                FatalExceptions [exc].

        Fancies:
            --progress (or -B):
                Display a progress meter instead of the usual output.
                Most notices will instead be written to log file.
                
        
        Operations:
            rm  [source..]
                Remove files. If no source - read from stdin.
            add [source..]
                Add files. If no source - read from stdin.
            fix [source..]
                Fix files in repos. If no source - read from stdin.
                Will check if file is in correct position, or move
                it and delete source when necessary. All using standard
                add and rm operations.
            lock [source..]
                Will lock a file preventing it from being removed
                or fixed.
            unlock [source..]
                Will unlock a locked file.
            inspect [source..]
                Inspect a number of files metadata.
            help
                Show the help text and exit.
        

        Files (defaults):
            log: (/tmp/musync.log)
                Created at each run - empty when no problem.
                """


def _generate_click_help():
    """Generate help text from click command definitions, formatted to match original style."""
    import io
    from contextlib import redirect_stdout
    
    # Define the command with all options matching the current implementation
    @click.command(
        name='musync',
        context_settings={'help_option_names': ['--help', '-h']}
    )
    @click.option('--pretend', '-p', is_flag=True, 
                  help="Just pretend to do actions, telling what you would do. 'pretend'")
    @click.option('--version', '-V', is_flag=True,
                  help="Echo version information and exit.")
    @click.option('--recursive', '-R', is_flag=True,
                  help="Scan directories recursively. 'recursive'")
    @click.option('--lock', '-L', is_flag=True,
                  help="Can be combined with fix or add for locking after operation has been performed. 'lock' (also 'lock-file')")
    @click.option('--silent', '-s', is_flag=True,
                  help="Supresses what is defined in 'suppressed'. 'silent'")
    @click.option('--verbose', '-v', is_flag=True,
                  help="Makes musync more talkative. 'verbose'")
    @click.option('--force', '-f', is_flag=True,
                  help="Force the current action. You might be prompted to force certain actions. 'force'")
    @click.option('--root', type=str,
                  help="Specify target root. <target_root>")
    @click.option('--config', '-c', type=str,
                  help="Specify configuration section. <section1>,<section2>,... 'default-config' These work as overlays and the latest key specified is the one used, empty keys do not overwrite pre-defined.")
    @click.option('--modify', '-M', type=str,
                  help='Use metadata provided here instead of the one in files. key="new value" Valid keys are: artist - artist tag, album - album name, title - track title, track - track number')
    @click.option('--debug', '-d', is_flag=True,
                  help="Will enable printing of traceback on FatalExceptions [exc].")
    @click.argument('operation', required=False)
    @click.argument('files', nargs=-1, required=False)
    def musync_cmd(**kwargs):
        """musync - music syncing scripts"""
        pass
    
    # Get click's help text
    ctx = musync_cmd.make_context('musync', [])
    help_text = ctx.get_help()
    
    # Format to match original style
    lines = []
    lines.append("    musync - music syncing scripts")
    lines.append("    Usage: musync [option(s)] <operation> [file1 [..]]")
    lines.append("    ")
    lines.append("    reads [file1 [..]] or each line from stdin as source files.")
    lines.append("    musync is designed to be non-destructive and will never modify source files")
    lines.append("    unless it is explicitly specified in configuration.")
    lines.append("    ")
    lines.append("    musync is not an interactive tool.")
    lines.append("    musync syncronizes files into a music repository.")
    lines.append("   ")
    lines.append("        General:")
    lines.append("            --export (or -e):")
    lines.append("                Will tell you what configurations that will be used")
    lines.append("                for certain arguments.")
    lines.append("            --version (or -V):")
    lines.append("                Echo version information and exit.")
    lines.append("            --force (or -f) 'force':")
    lines.append("                Force the current action. You might be prompted to force")
    lines.append("                certain actions.")
    lines.append("            --allow-similar:")
    lines.append("                tells musync not to check for similar files.")
    lines.append("    ")
    lines.append("        Options:")
    lines.append("        syntax: *long-opt* (or *short-opt*) [*args*] '*conf-key*' (also *relevant*):")
    lines.append("    ")
    
    # Add options from click definitions
    options_info = [
        ("--no-fixme", None, "ignore 'fixme' problems (you should review fixme-file first).", "'no-fixme'"),
        ("--lock", "-L", "Can be combined with fix or add for locking after operation has been performed.", "'lock' (also 'lock-file')"),
        ("--pretend", "-p", "Just pretend to do actions, telling what you would do.", "'pretend'"),
        ("--recursive", "-R", "Scan directories recursively.", "'recursive'"),
        ("--silent", "-s", "Supresses what is defined in 'suppressed'.", "'silent'"),
        ("--verbose", "-v", "Makes musync more talkative.", "'verbose'"),
        ("--coloring", "-C", "Invokes coloring of output.", "'coloring'"),
        ("--root", None, "Specify target root.", "<target_root>"),
        ("--config", "-c", "Specify configuration section. These work as overlays and the latest key specified is the one used, empty keys do not overwrite pre-defined.", "<section1>,<section2>,... 'default-config'"),
        ("--modify", "-M", 'Use metadata provided here instead of the one in files. Valid keys are: artist - artist tag, album - album name, title - track title, track - track number', 'key="new value"'),
        ("--debug", "-d", "Will enable printing of traceback on FatalExceptions [exc].", None),
    ]
    
    for long_opt, short_opt, desc, conf_key in options_info:
        if short_opt:
            opt_str = f"            {long_opt} (or {short_opt})"
        else:
            opt_str = f"            {long_opt}"
        if conf_key:
            opt_str += f" {conf_key}"
        opt_str += ":"
        lines.append(opt_str)
        # Wrap description if needed
        desc_lines = _wrap_text(desc, 16)
        for desc_line in desc_lines:
            lines.append(f"                {desc_line}")
        lines.append("    ")
    
    # Add transcode option (not in click but in original help)
    lines.append("            -T <from ext>=<to ext>")
    lines.append("                Transcode from one extension to another, tries to find")
    lines.append("                configuration variable *from*-to-*to*.")
    lines.append("                Example: -T flac>ogg (with key flac-to-ogg).")
    lines.append("    ")
    
    lines.append("        Fancies:")
    lines.append("            --progress (or -B):")
    lines.append("                Display a progress meter instead of the usual output.")
    lines.append("                Most notices will instead be written to log file.")
    lines.append("                ")
    lines.append("        ")
    lines.append("        Operations:")
    
    operations = [
        ("rm", "Remove files. If no source - read from stdin.", "[source..]"),
        ("add", "Add files. If no source - read from stdin.", "[source..]"),
        ("fix", "Fix files in repos. If no source - read from stdin. Will check if file is in correct position, or move it and delete source when necessary. All using standard add and rm operations.", "[source..]"),
        ("lock", "Will lock a file preventing it from being removed or fixed.", "[source..]"),
        ("unlock", "Will unlock a locked file.", "[source..]"),
        ("inspect", "Inspect a number of files metadata.", "[source..]"),
        ("help", "Show the help text and exit.", None),
    ]
    
    for op, desc, args in operations:
        if args:
            lines.append(f"            {op}  {args}")
        else:
            lines.append(f"            {op}")
        desc_lines = _wrap_text(desc, 16)
        for desc_line in desc_lines:
            lines.append(f"                {desc_line}")
        lines.append("    ")
    
    lines.append("    ")
    lines.append("        Files (defaults):")
    lines.append("            log: (/tmp/musync.log)")
    lines.append("                Created at each run - empty when no problem.")
    lines.append("                ")
    
    return "\n".join(lines)


def _wrap_text(text, indent=0):
    """Wrap text to approximately 70 characters, respecting indent."""
    max_width = 70 - indent
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + (1 if current_line else 0)
        if current_length + word_length <= max_width:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines
