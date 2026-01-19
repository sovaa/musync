"""Complete tests for musync entrypoint to increase coverage."""
import pytest
import sys
from unittest.mock import Mock, patch
from musync import entrypoint
from musync.errors import FatalException


@patch("sys.exit")
@patch("musync.opts.AppSession")
def test_entrypoint_general_exception(mock_app_session, mock_exit):
    """Test entrypoint() handling general Exception."""
    mock_app = Mock()
    mock_app.configured = True
    mock_app.args = ["add", "test.txt"]
    mock_app.lambdaenv.verbose = False
    mock_app.printer = Mock()
    mock_app.locker = Mock()
    mock_app.locker.stop = Mock()
    mock_app_session.return_value = mock_app
    
    with patch("musync.main", side_effect=Exception("General error")):
        entrypoint()
        mock_app.printer.error.assert_called()
        mock_exit.assert_called_with(1)


@patch("sys.exit")
@patch("musync.opts.AppSession")
def test_entrypoint_with_debug(mock_app_session, mock_exit):
    """Test entrypoint() with debug mode."""
    mock_app = Mock()
    mock_app.configured = True
    mock_app.args = ["add", "test.txt"]
    mock_app.lambdaenv.verbose = False
    mock_app.lambdaenv.debug = True
    mock_app.printer = Mock()
    mock_app.locker = Mock()
    mock_app.locker.stop = Mock()
    mock_app_session.return_value = mock_app
    
    with patch("musync.main", side_effect=FatalException("Test error")):
        with patch("traceback.format_exc") as mock_tb:
            entrypoint()
            mock_tb.assert_called()


@patch("sys.exit")
@patch("musync.opts.AppSession")
def test_entrypoint_systemexit(mock_app_session, mock_exit):
    """Test entrypoint() handling SystemExit."""
    mock_app = Mock()
    mock_app.configured = True
    mock_app.args = ["add", "test.txt"]
    mock_app.lambdaenv.verbose = False
    mock_app.printer = Mock()
    mock_app.locker = Mock()
    mock_app.locker.stop = Mock()
    mock_app_session.return_value = mock_app
    
    with patch("musync.main", side_effect=SystemExit(2)):
        entrypoint()
        mock_exit.assert_called_with(2)


@patch("sys.exit")
@patch("musync.opts.AppSession")
def test_entrypoint_verbose_stats(mock_app_session, mock_exit):
    """Test entrypoint() with verbose stats."""
    mock_app = Mock()
    mock_app.configured = True
    mock_app.args = ["add", "test.txt"]
    mock_app.lambdaenv.verbose = True
    mock_app.printer = Mock()
    mock_app.locker = Mock()
    mock_app.locker.stop = Mock()
    mock_app_session.return_value = mock_app
    
    with patch("musync.main", return_value=0):
        with patch("musync.op.handled_files", 5):
            with patch("musync.op.handled_dirs", 2):
                entrypoint()
                mock_app.printer.boldnotice.assert_called()
