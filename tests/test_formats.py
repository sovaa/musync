"""Tests for musync.formats module."""
import pytest
from unittest.mock import Mock, patch
import musync.formats


def test_formats_open_unsupported(tmp_path):
    """Test formats.open() with unsupported file."""
    test_file = tmp_path / "test.xyz"
    test_file.write_text("content")
    
    result = musync.formats.open(str(test_file))
    assert result is None


def test_formats_open_mp3(tmp_path):
    """Test formats.open() with MP3 file (mocked)."""
    test_file = tmp_path / "test.mp3"
    test_file.write_text("fake mp3")
    
    with patch("mutagen.File") as mock_file:
        mock_file.return_value = None
        result = musync.formats.open(str(test_file))
        # Should try to open with mutagen
        mock_file.assert_called()


def test_formats_open_mp4(tmp_path):
    """Test formats.open() with MP4 file."""
    test_file = tmp_path / "test.m4a"
    test_file.write_text("fake mp4")
    
    with patch("mutagen.File") as mock_file:
        mock_file.return_value = None
        result = musync.formats.open(str(test_file))
        mock_file.assert_called()


def test_formats_open_ogg(tmp_path):
    """Test formats.open() with OGG file."""
    test_file = tmp_path / "test.ogg"
    test_file.write_text("fake ogg")
    
    with patch("mutagen.File") as mock_file:
        mock_file.return_value = None
        result = musync.formats.open(str(test_file))
        mock_file.assert_called()
