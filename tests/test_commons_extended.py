"""Extended tests for musync.commons to increase coverage."""
import pytest
import os
from musync.commons import Path


def test_path_get_path_with_ext(mock_app, tmp_path):
    """Test Path.get_path() with extension."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Path(mock_app, str(test_file), ext="mp3")
    assert path.ext == "mp3"
    assert ".mp3" in path.path or "mp3" in path.path


def test_path_get_path_no_ext(mock_app, tmp_path):
    """Test Path.get_path() without extension."""
    test_file = tmp_path / "test"
    test_file.write_text("content")
    
    path = Path(mock_app, str(test_file), ext="")
    assert path.ext == ""
    assert path.path == str(test_file) or "test" in path.path


def test_path_with_custom_dir(mock_app, tmp_path):
    """Test Path with custom directory."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    custom_dir = tmp_path / "custom"
    custom_dir.mkdir()
    
    path = Path(mock_app, str(test_file), dir=str(custom_dir))
    assert custom_dir.name in path.dir or str(custom_dir) in path.dir


def test_path_with_custom_basename(mock_app, tmp_path):
    """Test Path with custom basename."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    path = Path(mock_app, str(test_file), basename="custom")
    assert "custom" in path.basename or path.basename == "custom"


def test_path_children_with_error(mock_app, tmp_path):
    """Test Path.children() with directory that causes OSError."""
    from unittest.mock import patch
    path = Path(mock_app, str(tmp_path))
    
    # Mock os.listdir to raise OSError
    with patch("os.listdir", side_effect=OSError("Permission denied")):
        children = list(path.children())
        assert len(children) == 0


def test_path_walk_directory_recursive(mock_app, tmp_path):
    """Test Path.walk() with directory recursively."""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    subdir = test_dir / "subdir"
    subdir.mkdir()
    test_file = subdir / "file.txt"
    test_file.write_text("content")
    
    path = Path(mock_app, str(test_dir))
    results = list(path.walk(None))
    # Should yield directory and its contents
    assert len(results) >= 1


def test_path_relativepath_not_in_root(mock_app, tmp_path):
    """Test Path.relativepath() when not in root."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    mock_app.lambdaenv.root = "/different/root"
    
    path = Path(mock_app, str(test_file))
    result = path.relativepath()
    assert result is False


def test_path_rmdir_not_empty(mock_app, tmp_path):
    """Test Path.rmdir() with non-empty directory."""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    test_file = test_dir / "file.txt"
    test_file.write_text("content")
    
    path = Path(mock_app, str(test_dir))
    path.rmdir()  # Should not remove non-empty directory
    assert test_dir.exists()
