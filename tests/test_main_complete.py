"""Complete tests for musync main function to increase coverage."""
import pytest
from unittest.mock import Mock, patch
from musync import main
from musync.errors import FatalException


def test_main_fix_operation(mock_app, tmp_path):
    """Test main() with fix operation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.args = ["fix", str(test_file)]
    
    with patch("musync.op.operate") as mock_operate:
        result = main(mock_app)
        assert result == 0
        mock_operate.assert_called_once()


def test_main_lock_operation(mock_app, tmp_path):
    """Test main() with lock operation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.args = ["lock", str(test_file)]
    
    with patch("musync.op.operate") as mock_operate:
        result = main(mock_app)
        assert result == 0
        mock_operate.assert_called_once()


def test_main_unlock_operation(mock_app, tmp_path):
    """Test main() with unlock operation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.args = ["unlock", str(test_file)]
    
    with patch("musync.op.operate") as mock_operate:
        result = main(mock_app)
        assert result == 0
        mock_operate.assert_called_once()


def test_main_sync_operation(mock_app, tmp_path):
    """Test main() with sync operation (alias for add)."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.args = ["sync", str(test_file)]
    
    with patch("musync.op.operate") as mock_operate:
        result = main(mock_app)
        assert result == 0
        mock_operate.assert_called_once()


def test_main_verbose_pretend(mock_app, tmp_path):
    """Test main() with verbose and pretend mode."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.args = ["add", str(test_file)]
    mock_app.lambdaenv.verbose = True
    mock_app.lambdaenv.pretend = True
    
    with patch("musync.op.operate"):
        result = main(mock_app)
        assert result == 0


def test_main_verbose_real(mock_app, tmp_path):
    """Test main() with verbose and real mode."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.args = ["add", str(test_file)]
    mock_app.lambdaenv.verbose = True
    mock_app.lambdaenv.pretend = False
    
    with patch("musync.op.operate"):
        result = main(mock_app)
        assert result == 0
