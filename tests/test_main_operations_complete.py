"""Complete tests for musync main operations to increase coverage."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from musync import op_add, op_remove, op_fix, op_lock, op_unlock, op_inspect
from musync.commons import Path


def test_op_add_with_lock_option(mock_app, tmp_path):
    """Test op_add() with lock option enabled."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    mock_app.lambdaenv.lock = True
    
    test_file = tmp_path / "source.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.isdir.return_value = False
    path.isfile.return_value = True
    path.path = str(test_file)
    path.meta = Mock()
    
    target = Mock()
    target.relativepath.return_value = "target.txt"
    target.path = str(tmp_path / "target.txt")
    target.isfile.return_value = False
    
    with patch("musync.dbman.build_target", return_value=target):
        with patch("musync.dbman.add"):
            with patch("musync.op_lock") as mock_lock:
                mock_app.locker.islocked.return_value = False
                op_add(mock_app, path)
                mock_lock.assert_called_once()


def test_op_remove_empty_dir_pretend(mock_app, tmp_path):
    """Test op_remove() with empty directory in pretend mode."""
    test_dir = tmp_path / "emptydir"
    test_dir.mkdir()
    
    path = Mock()
    path.isdir.return_value = True
    path.inroot.return_value = True
    path.isempty.return_value = True
    path.relativepath.return_value = "emptydir"
    path.path = str(test_dir)
    
    mock_app.lambdaenv.pretend = True
    op_remove(mock_app, path)
    mock_app.printer.notice.assert_called()


def test_op_remove_file_not_found(mock_app, tmp_path):
    """Test op_remove() with target file not found."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.isdir.return_value = False
    path.isfile.return_value = True
    path.meta = Mock()
    path.path = str(test_file)
    
    target = Mock()
    target.relativepath.return_value = "target.txt"
    target.isfile.return_value = False
    
    with patch("musync.dbman.build_target", return_value=target):
        mock_app.locker.islocked.return_value = False
        mock_app.locker.parentislocked.return_value = False
        op_remove(mock_app, path)
        mock_app.printer.warning.assert_called()


def test_op_fix_lock_file(mock_app, tmp_path):
    """Test op_fix() ignoring lock file."""
    mock_app.lambdaenv.root = str(tmp_path)
    lock_file = tmp_path / ".lock"
    lock_file.write_text("")
    
    path = Mock()
    path.inroot.return_value = True
    path.isfile.return_value = True
    path.path = str(lock_file)
    path.meta = None
    
    mock_app.lambdaenv.lockdb = Mock(return_value=str(lock_file))
    op_fix(mock_app, path)
    mock_app.printer.action.assert_called()


def test_op_fix_remove_bad_file(mock_app, tmp_path):
    """Test op_fix() removing file with bad metadata."""
    mock_app.lambdaenv.root = str(tmp_path)
    test_file = tmp_path / "bad.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.inroot.return_value = True
    path.isfile.return_value = True
    path.path = str(test_file)
    path.meta = None
    
    mock_app.lambdaenv.lockdb = Mock(return_value="")
    mock_app.lambdaenv.rm = Mock()
    op_fix(mock_app, path)
    mock_app.lambdaenv.rm.assert_called_once()


def test_op_fix_empty_dir(mock_app, tmp_path):
    """Test op_fix() with empty directory."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    mock_app.lambdaenv.lock = False
    test_dir = tmp_path / "emptydir"
    test_dir.mkdir()
    
    path = Mock()
    path.inroot.return_value = True
    path.isdir.return_value = True
    path.isempty.return_value = True
    path.relativepath.return_value = "emptydir"
    path.path = str(test_dir)
    path.rmdir = Mock()
    
    mock_app.locker.islocked.return_value = False
    mock_app.locker.parentislocked.return_value = False
    op_fix(mock_app, path)
    path.rmdir.assert_called_once()


def test_op_fix_empty_dir_pretend(mock_app, tmp_path):
    """Test op_fix() with empty directory in pretend mode."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = True
    test_dir = tmp_path / "emptydir"
    test_dir.mkdir()
    
    path = Mock()
    path.inroot.return_value = True
    path.isdir.return_value = True
    path.isempty.return_value = True
    path.relativepath.return_value = "emptydir"
    path.path = str(test_dir)
    
    mock_app.locker.islocked.return_value = False
    mock_app.locker.parentislocked.return_value = False
    op_fix(mock_app, path)
    mock_app.printer.action.assert_called()


def test_op_fix_dir_not_empty(mock_app, tmp_path):
    """Test op_fix() with non-empty directory."""
    mock_app.lambdaenv.root = str(tmp_path)
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    test_file = test_dir / "file.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.inroot.return_value = True
    path.isdir.return_value = True
    path.isempty.return_value = False
    path.relativepath.return_value = "testdir"
    path.path = str(test_dir)
    
    mock_app.locker.islocked.return_value = False
    mock_app.locker.parentislocked.return_value = False
    op_fix(mock_app, path)
    mock_app.printer.notice.assert_called()


def test_op_unlock_file_not_locked(mock_app, tmp_path):
    """Test op_unlock() with file that's not locked."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = False
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Mock()
    path.inroot.return_value = True
    path.isfile.return_value = True
    path.path = str(test_file)
    
    mock_app.locker.islocked.return_value = False
    mock_app.locker.parentislocked.return_value = False
    op_unlock(mock_app, path)
    mock_app.printer.warning.assert_called()
