"""Extended tests for musync main operations."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from musync import op_add, op_remove, op_fix, op_lock, op_unlock
from musync.commons import Path


def test_op_add_with_meta_and_target(mock_app, tmp_path):
    """Test op_add() with metadata and target."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    mock_app.lambdaenv.lock = False
    
    test_file = tmp_path / "source.txt"
    test_file.write_text("content")
    
    # Create a mock path with meta
    path = Mock()
    path.isdir.return_value = False
    path.isfile.return_value = True
    path.path = str(test_file)
    path.meta = Mock()
    path.meta.artist = "Artist"
    path.meta.album = "Album"
    
    target = Mock()
    target.relativepath.return_value = "target.txt"
    target.path = str(tmp_path / "target.txt")
    target.isfile.return_value = False
    
    with patch("musync.dbman.build_target", return_value=target):
        with patch("musync.dbman.add") as mock_add:
            mock_app.locker.islocked.return_value = False
            op_add(mock_app, path)
            mock_add.assert_called_once()


def test_op_add_locked(mock_app, tmp_path):
    """Test op_add() with locked target."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.isdir.return_value = False
    path.isfile.return_value = True
    path.path = str(test_file)
    path.meta = Mock()
    
    target = Mock()
    target.relativepath.return_value = "target.txt"
    
    with patch("musync.dbman.build_target", return_value=target):
        mock_app.locker.islocked.return_value = True
        op_add(mock_app, path)
        mock_app.printer.warning.assert_called()


def test_op_add_pretend(mock_app, tmp_path):
    """Test op_add() in pretend mode."""
    mock_app.lambdaenv.pretend = True
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.isdir.return_value = False
    path.isfile.return_value = True
    path.path = str(test_file)
    path.meta = Mock()
    
    target = Mock()
    target.relativepath.return_value = "target.txt"
    
    with patch("musync.dbman.build_target", return_value=target):
        mock_app.locker.islocked.return_value = False
        op_add(mock_app, path)
        mock_app.printer.notice.assert_called()
        mock_app.printer.action.assert_called()


def test_op_remove_empty_dir(mock_app, tmp_path):
    """Test op_remove() with empty directory."""
    test_dir = tmp_path / "emptydir"
    test_dir.mkdir()
    
    path = Mock()
    path.isdir.return_value = True
    path.inroot.return_value = True
    path.isempty.return_value = True
    path.relativepath.return_value = "emptydir"
    path.path = str(test_dir)
    path.rmdir = Mock()
    
    mock_app.lambdaenv.pretend = False
    op_remove(mock_app, path)
    path.rmdir.assert_called_once()


def test_op_remove_file_locked(mock_app, tmp_path):
    """Test op_remove() with locked file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.isdir.return_value = False
    path.isfile.return_value = True
    path.meta = Mock()
    path.path = str(test_file)
    
    target = Mock()
    target.relativepath.return_value = "target.txt"
    target.isfile.return_value = True
    
    with patch("musync.dbman.build_target", return_value=target):
        mock_app.locker.islocked.return_value = True
        op_remove(mock_app, path)
        mock_app.printer.warning.assert_called()


def test_op_fix_file_sane(mock_app, tmp_path):
    """Test op_fix() with file that's already in correct location."""
    mock_app.lambdaenv.root = str(tmp_path)
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.inroot.return_value = True
    path.isfile.return_value = True
    path.path = str(test_file)
    path.meta = Mock()
    path.relativepath.return_value = "test.txt"
    
    target = Mock()
    target.path = str(test_file)
    target.isfile.return_value = True
    target.islink.return_value = False
    target.relativepath.return_value = "test.txt"
    
    with patch("musync.dbman.build_target", return_value=target):
        mock_app.locker.islocked.return_value = False
        mock_app.locker.parentislocked.return_value = False
        op_fix(mock_app, path)
        mock_app.printer.notice.assert_called()


def test_op_fix_file_insane(mock_app, tmp_path):
    """Test op_fix() with file in wrong location."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    source_file = tmp_path / "source.txt"
    source_file.write_text("content")
    
    path = Mock()
    path.inroot.return_value = True
    path.isfile.return_value = True
    path.path = str(source_file)
    path.meta = Mock()
    path.relativepath.return_value = "source.txt"
    
    target = Mock()
    target.path = str(tmp_path / "target.txt")
    target.isfile.return_value = False
    target.islink.return_value = False
    target.relativepath.return_value = "target.txt"
    
    with patch("musync.dbman.build_target", return_value=target):
        with patch("musync.dbman.add") as mock_add:
            mock_app.locker.islocked.return_value = False
            mock_app.locker.parentislocked.return_value = False
            mock_app.lambdaenv.rm = Mock()
            op_fix(mock_app, path)
            mock_add.assert_called_once()


def test_op_lock_file(mock_app, tmp_path):
    """Test op_lock() with file."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.inroot.return_value = True
    path.isfile.return_value = True
    path.path = str(test_file)
    
    op_lock(mock_app, path)
    mock_app.locker.lock.assert_called_once()
    mock_app.printer.notice.assert_called()


def test_op_lock_directory(mock_app, tmp_path):
    """Test op_lock() with directory."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    
    path = Mock()
    path.inroot.return_value = True
    path.isdir.return_value = True
    path.path = str(test_dir)
    
    op_lock(mock_app, path)
    mock_app.locker.lock.assert_called_once()


def test_op_unlock_file(mock_app, tmp_path):
    """Test op_unlock() with file."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.inroot.return_value = True
    path.isfile.return_value = True
    path.path = str(test_file)
    path.parent.return_value = Mock()
    path.parent.return_value.path = str(tmp_path)
    
    mock_app.locker.islocked.return_value = True
    op_unlock(mock_app, path)
    mock_app.locker.unlock.assert_called_once()


def test_op_unlock_file_parent_locked(mock_app, tmp_path):
    """Test op_unlock() with file whose parent is locked."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.inroot.return_value = True
    path.isfile.return_value = True
    path.path = str(test_file)
    parent = Mock()
    parent.path = str(tmp_path)
    path.parent.return_value = parent
    
    mock_app.locker.islocked.return_value = False
    mock_app.locker.parentislocked.return_value = True
    op_unlock(mock_app, path)
    mock_app.printer.warning.assert_called()


def test_op_unlock_directory(mock_app, tmp_path):
    """Test op_unlock() with directory."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    
    path = Mock()
    path.inroot.return_value = True
    path.isdir.return_value = True
    path.path = str(test_dir)
    
    op_unlock(mock_app, path)
    mock_app.locker.unlock.assert_called_once()
