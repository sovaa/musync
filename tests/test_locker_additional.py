"""Additional tests for musync.locker module."""
import pytest
from unittest.mock import Mock
from musync.locker import LockFileDB
from musync.commons import Path


def test_lockfiledb_parentislocked(mock_app, tmp_path):
    """Test LockFileDB.parentislocked() method."""
    lock_file_path = str(tmp_path / ".lock")
    db = LockFileDB(mock_app, lock_file_path)
    mock_app.lambdaenv.root = str(tmp_path)
    
    # Lock parent directory
    parent_dir = tmp_path / "parent"
    parent_dir.mkdir()
    parent_path = Path(mock_app, str(parent_dir))
    db.lock(parent_path)
    db.stop()
    
    # Create file in parent
    test_file = parent_dir / "test.txt"
    test_file.write_text("content")
    file_path = Path(mock_app, str(test_file))
    
    # Reload db
    db2 = LockFileDB(mock_app, lock_file_path)
    assert db2.parentislocked(file_path)


def test_lockfiledb_stop_no_changes(mock_app, tmp_path):
    """Test LockFileDB.stop() with no changes."""
    lock_file_path = str(tmp_path / ".lock")
    db = LockFileDB(mock_app, lock_file_path)
    db.changed = False
    db.stop()  # Should not write anything


def test_lockfiledb_stop_with_removed(mock_app, tmp_path):
    """Test LockFileDB.stop() with removed items."""
    lock_file_path = str(tmp_path / ".lock")
    db = LockFileDB(mock_app, lock_file_path)
    db.changed = True
    db.removed = True
    db.DB = ["file1.txt", "file2.txt"]
    db.stop()
    
    # Verify file was written
    with open(lock_file_path, "r") as f:
        content = f.read()
        assert "file1.txt" in content
        assert "file2.txt" in content


def test_lockfiledb_stop_with_new(mock_app, tmp_path):
    """Test LockFileDB.stop() with new items."""
    lock_file_path = str(tmp_path / ".lock")
    db = LockFileDB(mock_app, lock_file_path)
    db.changed = True
    db.removed = False
    db.DB_NEWS = ["newfile.txt\n"]
    db.stop()
    
    # Verify file was appended to
    with open(lock_file_path, "r") as f:
        content = f.read()
        assert "newfile.txt" in content
