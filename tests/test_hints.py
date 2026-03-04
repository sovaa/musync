"""Tests for musync.hints module."""
import pytest
from unittest.mock import Mock, patch
import musync.hints
import musync.op


def test_print_hint(capsys):
    """print_hint prints HINT: prefix and text to stdout."""
    musync.hints.print_hint("Did you forget -R?")
    out, _ = capsys.readouterr()
    assert "HINT: Did you forget -R?" in out


def test_run_silent_no_print(mock_app, capsys):
    """run does nothing when app.lambdaenv.silent is True."""
    mock_app.lambdaenv.silent = True
    with patch.object(musync.op, "handled_files", 0):
        with patch.object(musync.op, "handled_dirs", 5):
            musync.hints.run(mock_app)
    out, _ = capsys.readouterr()
    assert "HINT:" not in out


def test_run_handled_files_zero_handled_dirs_positive_shows_hint(mock_app, capsys):
    """run prints recursive hint when handled_files==0 and handled_dirs>0."""
    mock_app.lambdaenv.silent = False
    with patch.object(musync.op, "handled_files", 0):
        with patch.object(musync.op, "handled_dirs", 3):
            musync.hints.run(mock_app)
    out, _ = capsys.readouterr()
    assert "HINT:" in out
    assert "recursive" in out or "-R" in out


def test_run_handled_files_positive_no_hint(mock_app, capsys):
    """run does not print hint when handled_files > 0."""
    mock_app.lambdaenv.silent = False
    with patch.object(musync.op, "handled_files", 1):
        with patch.object(musync.op, "handled_dirs", 0):
            musync.hints.run(mock_app)
    out, _ = capsys.readouterr()
    assert "HINT:" not in out


def test_run_handled_dirs_zero_no_hint(mock_app, capsys):
    """run does not print hint when handled_dirs is 0."""
    mock_app.lambdaenv.silent = False
    with patch.object(musync.op, "handled_files", 0):
        with patch.object(musync.op, "handled_dirs", 0):
            musync.hints.run(mock_app)
    out, _ = capsys.readouterr()
    assert "HINT:" not in out
