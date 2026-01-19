"""Tests for op_fix to increase coverage."""
import pytest
from unittest.mock import Mock, patch
from musync import op_fix


def test_op_fix_file_sane_path_match(mock_app, tmp_path):
    """Test op_fix() with file where source and target paths match."""
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
    target.path = str(test_file)  # Same path
    target.relativepath.return_value = "test.txt"
    
    with patch("musync.dbman.build_target", return_value=target):
        mock_app.locker.islocked.return_value = False
        mock_app.locker.parentislocked.return_value = False
        op_fix(mock_app, path)
        mock_app.printer.notice.assert_called()


def test_op_fix_file_insane_pretend(mock_app, tmp_path):
    """Test op_fix() with file in wrong location in pretend mode."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.pretend = True
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
        mock_app.locker.islocked.return_value = False
        mock_app.locker.parentislocked.return_value = False
        op_fix(mock_app, path)
        mock_app.printer.action.assert_called()


def test_op_fix_file_insane_remove_source(mock_app, tmp_path):
    """Test op_fix() removing source file after moving."""
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
        with patch("musync.dbman.add"):
            mock_app.locker.islocked.return_value = False
            mock_app.locker.parentislocked.return_value = False
            mock_app.lambdaenv.rm = Mock()
            op_fix(mock_app, path)
            mock_app.lambdaenv.rm.assert_called_once()


def test_op_fix_file_insane_with_link(mock_app, tmp_path):
    """Test op_fix() with file that is a link."""
    mock_app.lambdaenv.root = str(tmp_path)
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
    target.islink.return_value = True  # It's a link
    target.relativepath.return_value = "target.txt"
    
    with patch("musync.dbman.build_target", return_value=target):
        mock_app.locker.islocked.return_value = False
        mock_app.locker.parentislocked.return_value = False
        op_fix(mock_app, path)
        # Should not add if target is a link
        mock_app.printer.notice.assert_called()
