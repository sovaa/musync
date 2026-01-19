"""Tests for musync main operations."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from musync import op_add, op_remove, op_fix, op_lock, op_unlock, op_inspect


def test_op_add_directory(mock_app, tmp_path):
    """Test op_add() with directory."""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    path = Mock()
    path.isdir.return_value = True
    path.path = str(test_dir)
    
    op_add(mock_app, path)
    mock_app.printer.notice.assert_called()


def test_op_add_no_meta(mock_app, tmp_path):
    """Test op_add() with file without metadata."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Mock()
    path.isdir.return_value = False
    path.isfile.return_value = True
    path.path = str(test_file)
    path.meta = None
    
    op_add(mock_app, path)
    mock_app.printer.warning.assert_called()


def test_op_remove_directory(mock_app, tmp_path):
    """Test op_remove() with directory."""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    path = Mock()
    path.isdir.return_value = True
    path.inroot.return_value = False
    path.path = str(test_dir)
    
    op_remove(mock_app, path)
    mock_app.printer.warning.assert_called()


def test_op_remove_file_not_in_root(mock_app, tmp_path):
    """Test op_remove() with file not in root."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Mock()
    path.isdir.return_value = False
    path.isfile.return_value = True
    path.meta = Mock()
    path.inroot.return_value = False
    path.path = str(test_file)
    
    with patch("musync.dbman.build_target") as mock_build:
        mock_target = Mock()
        mock_target.relativepath.return_value = "test.txt"
        mock_build.return_value = mock_target
        op_remove(mock_app, path)


def test_op_fix_not_in_root(mock_app, tmp_path):
    """Test op_fix() with file not in root."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Mock()
    path.inroot.return_value = False
    path.path = str(test_file)
    
    op_fix(mock_app, path)
    mock_app.printer.warning.assert_called()


def test_op_lock_not_in_root(mock_app, tmp_path):
    """Test op_lock() with file not in root."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Mock()
    path.inroot.return_value = False
    path.path = str(test_file)
    
    op_lock(mock_app, path)
    mock_app.printer.warning.assert_called()


def test_op_lock_pretend(mock_app, tmp_path):
    """Test op_lock() in pretend mode."""
    mock_app.lambdaenv.pretend = True
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Mock()
    path.inroot.return_value = True
    path.path = str(test_file)
    
    op_lock(mock_app, path)
    mock_app.printer.action.assert_called()


def test_op_unlock_not_in_root(mock_app, tmp_path):
    """Test op_unlock() with file not in root."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Mock()
    path.inroot.return_value = False
    path.path = str(test_file)
    
    op_unlock(mock_app, path)
    mock_app.printer.warning.assert_called()


def test_op_unlock_pretend(mock_app, tmp_path):
    """Test op_unlock() in pretend mode."""
    mock_app.lambdaenv.pretend = True
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Mock()
    path.inroot.return_value = True
    path.path = str(test_file)
    
    op_unlock(mock_app, path)
    mock_app.printer.action.assert_called()


def test_op_inspect_not_file(mock_app, tmp_path):
    """Test op_inspect() with non-file."""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    path = Mock()
    path.isfile.return_value = False
    path.path = str(test_dir)
    
    op_inspect(mock_app, path)
    mock_app.printer.warning.assert_called()


def test_op_inspect_no_meta(mock_app, tmp_path):
    """Test op_inspect() with file without metadata."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Mock()
    path.isfile.return_value = True
    path.meta = None
    path.path = str(test_file)
    
    op_inspect(mock_app, path)
    mock_app.printer.warning.assert_called()


def test_op_inspect_with_meta(mock_app, tmp_path):
    """Test op_inspect() with file with metadata."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Mock()
    path.isfile.return_value = True
    path.meta = Mock()
    path.meta.filename = "test.txt"
    path.meta.artist = "Artist"
    path.meta.album = "Album"
    path.meta.title = "Title"
    path.meta.track = "1"
    path.meta.year = "2020"
    path.path = str(test_file)
    
    mock_app.lambdaenv.targetpath = lambda x: "target/path"
    
    op_inspect(mock_app, path)
    mock_app.printer.boldnotice.assert_called()
    assert mock_app.printer.blanknotice.call_count >= 5
