"""Pytest configuration and fixtures."""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the parent directory to the path so we can import musync
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_app():
    """Create a mock app object for testing."""
    from unittest.mock import Mock, MagicMock
    
    app = Mock()
    app.lambdaenv = Mock()
    app.lambdaenv.root = "/tmp/music"
    app.lambdaenv.pretend = False
    app.lambdaenv.verbose = False
    app.lambdaenv.debug = False
    app.lambdaenv.silent = False
    app.lambdaenv.suppressed = []
    app.lambdaenv.recursive = False
    app.lambdaenv.modify = {}
    app.printer = Mock()
    app.locker = Mock()
    app.configured = True
    app.args = []
    app.settings = Mock()
    app.settings.targetpath = "targetpath"
    return app
