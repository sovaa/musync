## [Unreleased]

### Added

- **Fix (op_fix)**: When target path is a symlink, print a notice ("target is link - ...") instead of silently skipping.
- **Tests**: New and extended tests for hints, dbman, rulelexer, formats, printer, opts; coverage raised to 80%+.

### Changed

- **Version**: Bumped to 0.7.0 for modern Python (3.12+).
- **musync/**: Modernized for Python 3.12–3.13: f-strings, type hints, pathlib, context managers (`with open(...)`) for all file handling, match/case in opts, literal list/dict (`[]`/`{}`), and direct boolean returns in locker.
- **Python**: Requires Python 3.12+ (dropped 3.7–3.11).
- **opts**: Config parsing uses `RawConfigParser.read_file()` instead of deprecated `readfp()`.
- **printer**: `_unicodeencode` now correctly handles `bytes` (decode to str).
- **hints**: Use f-string for hint message.

### Fixed

- **printer**: On Windows, skip curses entirely (no import, no setupterm) to avoid hang/memory blowup; make curses optional on other platforms when unavailable.
- **entrypoint**: Handle `--version` / `-V` before creating AppSession so version prints and exits without loading config or printer (avoids startup hang on Windows).
- **opts**: Mutable default argument in `LambdaEnviron.__init__` (use `d=None`).
- **rulelexer**: Mutable default argument in `Reader.__init__` (use `ignore=None`).

### Added (Phase 2)

- **errors, hints**: Type hints on public functions; `errors` uses `super().__init__` and no longer shadows builtin `str`.
