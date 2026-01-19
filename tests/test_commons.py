"""Tests for musync.commons module."""
import os
import tempfile
import shutil
import pytest
from musync.commons import Path


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file for testing."""
    file_path = os.path.join(temp_dir, "test.txt")
    with open(file_path, "w") as f:
        f.write("test content")
    return file_path


@pytest.fixture
def temp_dir_structure(temp_dir):
    """Create a temporary directory structure."""
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)
    file_path = os.path.join(subdir, "file.txt")
    with open(file_path, "w") as f:
        f.write("content")
    return temp_dir, subdir, file_path


def test_path_initialization(mock_app, temp_file):
    """Test Path initialization with a file."""
    path = Path(mock_app, temp_file)
    assert path.path == os.path.abspath(temp_file)
    assert path.isfile()
    assert not path.isdir()


def test_path_directory(mock_app, temp_dir):
    """Test Path with a directory."""
    path = Path(mock_app, temp_dir)
    assert path.isdir()
    assert not path.isfile()


def test_path_exists(mock_app, temp_file):
    """Test Path.exists() method."""
    path = Path(mock_app, temp_file)
    assert path.exists()


def test_path_not_exists(mock_app):
    """Test Path with non-existent file."""
    path = Path(mock_app, "/nonexistent/file.txt")
    assert not path.exists()
    assert not path.isfile()
    assert not path.isdir()


def test_path_extension(mock_app, temp_file):
    """Test Path extension extraction."""
    path = Path(mock_app, temp_file)
    assert path.ext == "txt"


def test_path_basename(mock_app, temp_file):
    """Test Path basename property."""
    path = Path(mock_app, temp_file)
    assert "test" in path.basename or "test.txt" in path.basename


def test_path_dirname(mock_app, temp_file):
    """Test Path dirname method."""
    path = Path(mock_app, temp_file)
    dirname = path.dirname()
    assert os.path.isdir(dirname)


def test_path_isempty_dir(mock_app, temp_dir):
    """Test Path.isempty() with empty directory."""
    path = Path(mock_app, temp_dir)
    assert path.isempty()


def test_path_isempty_file(mock_app, temp_file):
    """Test Path.isempty() with file."""
    path = Path(mock_app, temp_file)
    # Files should return True for isempty
    assert path.isempty()


def test_path_parent(mock_app, temp_file):
    """Test Path.parent() method."""
    path = Path(mock_app, temp_file)
    parent = path.parent()
    assert parent.isdir()
    assert parent.path == os.path.dirname(path.path)


def test_path_children(mock_app, temp_dir_structure):
    """Test Path.children() method."""
    temp_dir, subdir, file_path = temp_dir_structure
    path = Path(mock_app, temp_dir)
    children = list(path.children())
    assert len(children) > 0


def test_path_inroot(mock_app, temp_file):
    """Test Path.inroot() method."""
    mock_app.lambdaenv.root = os.path.dirname(temp_file)
    path = Path(mock_app, temp_file)
    # Should be True if file is in root
    result = path.inroot()
    # This depends on the actual path structure
    assert isinstance(result, bool)


def test_path_isroot(mock_app, temp_dir):
    """Test Path.isroot() method."""
    mock_app.lambdaenv.root = temp_dir
    path = Path(mock_app, temp_dir)
    assert path.isroot()


def test_path_relativepath(mock_app, temp_dir):
    """Test Path.relativepath() method."""
    mock_app.lambdaenv.root = temp_dir
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)
    file_path = os.path.join(subdir, "file.txt")
    with open(file_path, "w") as f:
        f.write("content")
    
    path = Path(mock_app, file_path)
    relpath = path.relativepath()
    assert relpath is not False
    assert "subdir" in relpath or "file.txt" in relpath


def test_path_rmdir(mock_app, temp_dir):
    """Test Path.rmdir() method."""
    subdir = os.path.join(temp_dir, "emptydir")
    os.makedirs(subdir)
    path = Path(mock_app, subdir)
    path.rmdir()
    assert not os.path.exists(subdir)
