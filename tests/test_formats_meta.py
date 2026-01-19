"""Tests for musync.formats.meta module."""
import pytest
from unittest.mock import Mock
from musync.formats.meta import MetaFile


def test_metafile_initialization():
    """Test MetaFile initialization."""
    mock_file = Mock()
    mock_file.filename = "/path/to/test.mp3"
    tags = {}
    
    meta = MetaFile(mock_file, tags)
    assert meta.album is None
    assert meta.artist is None
    assert meta.title is None
    assert meta.track is None
    assert meta.year is None
    assert meta.filename == "test.mp3"


def test_metafile_extension_extraction():
    """Test MetaFile extension extraction."""
    mock_file = Mock()
    mock_file.filename = "/path/to/test.mp3"
    tags = {}
    
    meta = MetaFile(mock_file, tags)
    assert meta.ext == "mp3"


def test_metafile_with_tags():
    """Test MetaFile with tags."""
    mock_file = Mock()
    mock_file.filename = "/path/to/test.mp3"
    
    class TestMetaFile(MetaFile):
        __translate__ = {
            "artist": "artist",
            "album": "album",
            "title": "title",
        }
    
    tags = {
        "ARTIST": ["Test Artist"],
        "ALBUM": ["Test Album"],
        "TITLE": ["Test Title"],
    }
    
    meta = TestMetaFile(mock_file, tags)
    assert meta.artist == "Test Artist"
    assert meta.album == "Test Album"
    assert meta.title == "Test Title"


def test_metafile_case_insensitive_tags():
    """Test MetaFile case-insensitive tag matching."""
    mock_file = Mock()
    mock_file.filename = "/path/to/test.mp3"
    
    class TestMetaFile(MetaFile):
        __translate__ = {
            "artist": "artist",
        }
    
    tags = {
        "artist": ["Test Artist"],  # lowercase
    }
    
    meta = TestMetaFile(mock_file, tags)
    assert meta.artist == "Test Artist"


def test_metafile_no_extension():
    """Test MetaFile with filename without extension."""
    mock_file = Mock()
    mock_file.filename = "/path/to/test"
    tags = {}
    
    meta = MetaFile(mock_file, tags)
    # Should handle missing extension gracefully
    assert meta.filename == "test"
