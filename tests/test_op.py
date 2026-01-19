"""Tests for musync.op module."""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import musync.op
from musync.errors import FatalException, WarningException


def test_readpaths_file(mock_app, tmp_path):
    """Test readpaths() with a file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    paths = list(musync.op.readpaths(mock_app, str(test_file), False))
    assert len(paths) == 1
    assert paths[0].isfile()


def test_readpaths_directory(mock_app, tmp_path):
    """Test readpaths() with a directory."""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    
    paths = list(musync.op.readpaths(mock_app, str(test_dir), False))
    assert len(paths) == 1
    assert paths[0].isdir()


def test_readpaths_recursive(mock_app, tmp_path):
    """Test readpaths() with recursive option."""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    test_file = test_dir / "file.txt"
    test_file.write_text("content")
    
    mock_app.lambdaenv.recursive = True
    paths = list(musync.op.readpaths(mock_app, str(test_dir), False))
    # Should include both directory and file
    assert len(paths) >= 1


def test_readargs_with_args(mock_app, tmp_path):
    """Test readargs() with command line arguments."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    args = [str(test_file)]
    paths = list(musync.op.readargs(mock_app, args, False))
    assert len(paths) == 1


@patch("sys.stdin")
def test_readargs_from_stdin(mock_stdin, mock_app, tmp_path):
    """Test readargs() reading from stdin."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    mock_stdin.readline.side_effect = [str(test_file) + "\n", ""]
    paths = list(musync.op.readargs(mock_app, [], False))
    assert len(paths) >= 1


def test_operate_basic(mock_app, tmp_path):
    """Test operate() function with a simple callback."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    mock_app.args = ["add", str(test_file)]
    call_count = [0]
    
    def mock_call(app, path):
        call_count[0] += 1
    
    musync.op.operate(mock_app, mock_call)
    assert call_count[0] == 1


def test_operate_with_warning_exception(mock_app, tmp_path):
    """Test operate() handling WarningException."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    mock_app.args = ["add", str(test_file)]
    
    def mock_call(app, path):
        raise WarningException("Test warning")
    
    # Should not raise, but print warning
    musync.op.operate(mock_app, mock_call)
    # Verify warning was called
    assert mock_app.printer.warning.called


def test_operate_with_interrupt(mock_app, tmp_path):
    """Test operate() handling interrupt."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    mock_app.args = ["add", str(test_file)]
    musync.sign.Interrupt = True
    
    def mock_call(app, path):
        pass
    
    with pytest.raises(FatalException):
        musync.op.operate(mock_app, mock_call)
    
    musync.sign.Interrupt = False  # Reset
