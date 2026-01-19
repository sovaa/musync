"""Tests for musync.dbman module."""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from musync.commons import Path
from musync.dbman import build_target


def test_build_target_basic(mock_app, tmp_path):
    """Test build_target() basic functionality."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.targetpath = lambda meta: "Artist/Album/track.mp3"
    
    # Create a mock source with meta
    source = Mock()
    source.meta = Mock()
    source.meta.artist = "Artist"
    source.meta.album = "Album"
    source.meta.title = "Track"
    
    target = build_target(mock_app, source)
    assert target is not None


def test_build_target_with_meta(mock_app, tmp_path):
    """Test build_target() with metadata."""
    mock_app.lambdaenv.root = str(tmp_path)
    mock_app.lambdaenv.targetpath = lambda meta: f"{meta.artist}/{meta.album}/{meta.title}.mp3"
    
    source = Mock()
    source.meta = Mock()
    source.meta.artist = "Test Artist"
    source.meta.album = "Test Album"
    source.meta.title = "Test Track"
    
    target = build_target(mock_app, source)
    assert target is not None
