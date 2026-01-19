"""Additional tests for musync.commons Path.walk method."""
import pytest
import os
from musync.commons import Path


def test_path_walk_file(mock_app, tmp_path):
    """Test Path.walk() with a file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Path(mock_app, str(test_file))
    
    results = list(path.walk(None))
    assert len(results) == 1
    assert results[0].isfile()


def test_path_walk_directory(mock_app, tmp_path):
    """Test Path.walk() with a directory."""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    subdir = test_dir / "subdir"
    subdir.mkdir()
    test_file = subdir / "file.txt"
    test_file.write_text("content")
    
    path = Path(mock_app, str(test_dir))
    results = list(path.walk(None))
    # Should yield the directory and its children
    assert len(results) >= 1
