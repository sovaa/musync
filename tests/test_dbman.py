"""Tests for musync.dbman module."""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from musync.commons import Path
from musync.dbman import build_target, hash_get, add, remove
from musync.errors import FatalException


def test_hash_get_delegates_to_lambdaenv(mock_app):
    """hash_get calls app.lambdaenv.hash with path and returns result."""
    mock_app.lambdaenv.hash = Mock(return_value="abc123")
    result = hash_get(mock_app, "/some/path")
    mock_app.lambdaenv.hash.assert_called_once_with("/some/path")
    assert result == "abc123"


def test_add_parent_creation_success(mock_app, tmp_path):
    """add creates parent directory when t.parent() is not a dir."""
    sub = tmp_path / "Artist" / "Album"
    p = Mock()
    p.path = str(tmp_path / "source.mp3")
    t = Mock()
    t.path = str(sub / "track.mp3")
    t.dir = str(sub)
    t.parent = Mock(return_value=Mock(isdir=Mock(return_value=False)))
    t.exists = Mock(return_value=False)
    t.islink = Mock(return_value=False)
    mock_app.lambdaenv.force = False
    mock_app.lambdaenv.checkhash = False
    with patch("os.makedirs") as mock_makedirs:
        add(mock_app, p, t)
    mock_makedirs.assert_called_with(t.dir)
    mock_app.lambdaenv.add.assert_called_once_with(p.path, t.path)


def test_add_parent_creation_oserror_raises_fatal(mock_app, tmp_path):
    """add raises FatalException when makedirs raises OSError."""
    p = Mock()
    p.path = str(tmp_path / "source.mp3")
    t = Mock()
    t.path = str(tmp_path / "a" / "b" / "c.mp3")
    t.dir = str(tmp_path / "a" / "b")
    t.parent = Mock(return_value=Mock(isdir=Mock(return_value=False)))
    t.exists = Mock(return_value=False)
    t.islink = Mock(return_value=False)
    with patch("os.makedirs", side_effect=OSError("Permission denied")):
        with pytest.raises(FatalException) as exc_info:
            add(mock_app, p, t)
        assert "Permission denied" in str(exc_info.value)


def test_add_source_and_target_same_warns_and_returns(mock_app):
    """add prints warning and returns when source and target path are the same."""
    p = Mock()
    t = Mock()
    p.path = t.path = "/same/path"
    t.parent = Mock(return_value=Mock(isdir=Mock(return_value=True)))
    add(mock_app, p, t)
    mock_app.printer.warning.assert_called_once()
    mock_app.lambdaenv.add.assert_not_called()


def test_add_exists_no_force_warns_and_returns(mock_app):
    """add warns and returns when target exists and force is False."""
    p = Mock()
    p.path = "/src"
    t = Mock()
    t.path = "/tgt"
    t.parent = Mock(return_value=Mock(isdir=Mock(return_value=True)))
    t.exists = Mock(return_value=True)
    t.islink = Mock(return_value=False)
    mock_app.lambdaenv.force = False
    add(mock_app, p, t)
    mock_app.printer.warning.assert_called_once()
    mock_app.lambdaenv.add.assert_not_called()


def test_add_exists_force_removes_then_adds(mock_app):
    """add with force removes existing target then adds."""
    p = Mock()
    p.path = "/src"
    t = Mock()
    t.path = "/tgt"
    t.parent = Mock(return_value=Mock(isdir=Mock(return_value=True)))
    t.exists = Mock(return_value=True)
    t.islink = Mock(return_value=False)
    mock_app.lambdaenv.force = True
    mock_app.lambdaenv.checkhash = False
    add(mock_app, p, t)
    mock_app.lambdaenv.rm.assert_called_once_with(t)
    mock_app.lambdaenv.add.assert_called_once_with(p.path, t.path)


def test_add_no_checkhash_success(mock_app):
    """add without checkhash calls lambdaenv.add once and returns."""
    p = Mock()
    p.path = "/src"
    t = Mock()
    t.path = "/tgt"
    t.parent = Mock(return_value=Mock(isdir=Mock(return_value=True)))
    t.exists = Mock(return_value=False)
    t.islink = Mock(return_value=False)
    mock_app.lambdaenv.checkhash = False
    result = add(mock_app, p, t)
    mock_app.lambdaenv.add.assert_called_once_with(p.path, t.path)
    assert result is True


def test_add_checkhash_match_prints_notice(mock_app):
    """add with checkhash and matching hashes prints notice."""
    p = Mock()
    p.path = "/src"
    t = Mock()
    t.path = "/tgt"
    t.parent = Mock(return_value=Mock(isdir=Mock(return_value=True)))
    t.exists = Mock(return_value=False)
    t.islink = Mock(return_value=False)
    mock_app.lambdaenv.checkhash = True
    mock_app.lambdaenv.hash = Mock(return_value="samehash")
    add(mock_app, p, t)
    mock_app.lambdaenv.add.assert_called_once_with(p.path, t.path)
    mock_app.printer.notice.assert_called_once()


def test_add_checkhash_mismatch_retries(mock_app):
    """add with checkhash mismatch prints warning and retries (up to limit)."""
    p = Mock()
    p.path = "/src"
    t = Mock()
    t.path = "/tgt"
    t.parent = Mock(return_value=Mock(isdir=Mock(return_value=True)))
    t.exists = Mock(return_value=False)
    t.islink = Mock(return_value=False)
    mock_app.lambdaenv.checkhash = True
    # Each attempt: 2 hash calls (parity, check). Need 5+ attempts to hit FatalException.
    mock_app.lambdaenv.hash = Mock(side_effect=["h1", "h2"] * 5)
    with pytest.raises(FatalException) as exc_info:
        add(mock_app, p, t)
    assert "many" in str(exc_info.value).lower() or "times" in str(exc_info.value).lower()
    assert mock_app.lambdaenv.add.call_count >= 2


def test_add_source_missing_on_retry_raises_fatal(mock_app, tmp_path):
    """add raises FatalException when source no longer exists on retry."""
    tgt = tmp_path / "tgt.mp3"
    p = Mock()
    p.path = str(tmp_path / "src.mp3")
    p.exists = Mock(return_value=False)  # when attempts > 0 we check and raise
    t = Mock()
    t.path = str(tgt)
    t.parent = Mock(return_value=Mock(isdir=Mock(return_value=True)))
    t.exists = Mock(return_value=False)
    t.islink = Mock(return_value=False)
    mock_app.lambdaenv.checkhash = True
    mock_app.lambdaenv.hash = Mock(side_effect=["h1", "h2"])  # mismatch so one retry
    with pytest.raises(FatalException) as exc_info:
        add(mock_app, p, t)
    assert "no longer exists" in str(exc_info.value)


def test_remove_same_path_no_force_warns_and_returns(mock_app, tmp_path):
    """remove warns and returns when target path equals source and force is False."""
    p = Mock()
    t = Mock()
    p.path = t.path = "/same/path"
    mock_app.lambdaenv.force = False
    remove(mock_app, p, t)
    mock_app.printer.warning.assert_called_once()
    mock_app.lambdaenv.rm.assert_not_called()


def test_remove_same_path_with_force_calls_rm(mock_app):
    """remove with force calls lambdaenv.rm even when target equals source."""
    p = Mock()
    t = Mock()
    p.path = t.path = "/same/path"
    mock_app.lambdaenv.force = True
    result = remove(mock_app, p, t)
    mock_app.lambdaenv.rm.assert_called_once_with(t)
    assert result is True


def test_remove_different_path_calls_rm(mock_app):
    """remove calls lambdaenv.rm when target differs from source."""
    p = Mock()
    t = Mock()
    p.path = "/source"
    t.path = "/target"
    mock_app.lambdaenv.force = False
    result = remove(mock_app, p, t)
    mock_app.lambdaenv.rm.assert_called_once_with(t)
    assert result is True


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
