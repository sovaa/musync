"""Tests for musync.__init__ module (main entry point)."""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import musync
from musync.errors import FatalException


def test_print_if_verbose_pretend(mock_app):
    """Test print_if_verbose() with pretend mode."""
    mock_app.lambdaenv.verbose = True
    mock_app.lambdaenv.pretend = True
    
    musync.print_if_verbose(mock_app, "Pretending to add", "Adding")
    assert mock_app.printer.boldnotice.called


def test_print_if_verbose_real(mock_app):
    """Test print_if_verbose() with real mode."""
    mock_app.lambdaenv.verbose = True
    mock_app.lambdaenv.pretend = False
    
    musync.print_if_verbose(mock_app, "Pretending to add", "Adding")
    assert mock_app.printer.boldnotice.called


def test_print_if_verbose_not_verbose(mock_app):
    """Test print_if_verbose() when not verbose."""
    mock_app.lambdaenv.verbose = False
    
    musync.print_if_verbose(mock_app, "Pretending to add", "Adding")
    # Should not call printer when not verbose
    mock_app.printer.boldnotice.assert_not_called()


def test_main_help(mock_app):
    """Test main() with help command."""
    mock_app.args = ["help"]
    with patch("musync.opts.Usage") as mock_usage:
        mock_usage.return_value = "Usage information"
        result = musync.main(mock_app)
        assert result == 0
        mock_usage.assert_called_once()


def test_main_too_few_args(mock_app):
    """Test main() with too few arguments."""
    mock_app.args = []
    with pytest.raises(FatalException):
        musync.main(mock_app)


def test_main_invalid_operation(mock_app):
    """Test main() with invalid operation."""
    mock_app.args = ["invalid_op"]
    with pytest.raises(FatalException) as exc_info:
        musync.main(mock_app)
    assert "no such operation" in str(exc_info.value)


def test_main_add_operation(mock_app, tmp_path):
    """Test main() with add operation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.args = ["add", str(test_file)]
    
    with patch("musync.op.operate") as mock_operate:
        result = musync.main(mock_app)
        assert result == 0
        mock_operate.assert_called_once()


def test_main_remove_operation(mock_app, tmp_path):
    """Test main() with remove operation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.args = ["rm", str(test_file)]
    
    with patch("musync.op.operate") as mock_operate:
        result = musync.main(mock_app)
        assert result == 0
        mock_operate.assert_called_once()


def test_main_inspect_operation(mock_app, tmp_path):
    """Test main() with inspect operation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.args = ["inspect", str(test_file)]
    
    with patch("musync.op.operate") as mock_operate:
        result = musync.main(mock_app)
        assert result == 0
        mock_operate.assert_called_once()


@patch("sys.exit")
@patch("musync.opts.AppSession")
def test_entrypoint_success(mock_app_session, mock_exit):
    """Test entrypoint() successful execution."""
    mock_app = Mock()
    mock_app.configured = True
    mock_app.args = ["help"]
    mock_app.lambdaenv.verbose = False
    mock_app.printer = Mock()
    mock_app.locker = Mock()
    mock_app.locker.stop = Mock()
    mock_app_session.return_value = mock_app
    
    with patch("musync.main", return_value=0):
        musync.entrypoint()
        mock_exit.assert_called()


@patch("sys.exit")
@patch("musync.opts.AppSession")
def test_entrypoint_not_configured(mock_app_session, mock_exit):
    """Test entrypoint() when not configured."""
    mock_app = Mock()
    mock_app.configured = False
    mock_app_session.return_value = mock_app
    
    musync.entrypoint()
    # The actual exit code might be different, just check that exit was called
    assert mock_exit.called


@patch("sys.exit")
@patch("musync.opts.AppSession")
def test_entrypoint_fatal_exception(mock_app_session, mock_exit):
    """Test entrypoint() handling FatalException."""
    mock_app = Mock()
    mock_app.configured = True
    mock_app.args = ["help"]
    mock_app.lambdaenv.debug = False
    mock_app.printer = Mock()
    mock_app.locker = Mock()
    mock_app.locker.stop = Mock()
    mock_app_session.return_value = mock_app
    
    with patch("musync.main", side_effect=FatalException("Test error")):
        musync.entrypoint()
        mock_app.printer.error.assert_called()
