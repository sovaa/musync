"""Tests for musync.locker module."""
import os
import tempfile
import pytest
from musync.locker import LockFileDB
from musync.commons import Path


@pytest.fixture
def lock_file_path(tmp_path):
    """Create a temporary lock file path."""
    return str(tmp_path / ".lock")


@pytest.fixture
def lock_db(mock_app, lock_file_path):
    """Create a LockFileDB instance."""
    return LockFileDB(mock_app, lock_file_path)


def test_lockfiledb_initialization(mock_app, lock_file_path):
    """Test LockFileDB initialization."""
    db = LockFileDB(mock_app, lock_file_path)
    assert db.app == mock_app
    assert db.lock_path == lock_file_path
    assert isinstance(db.DB, list)


def test_lockfiledb_creates_file(mock_app, lock_file_path):
    """Test LockFileDB creates lock file if it doesn't exist."""
    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)
    
    db = LockFileDB(mock_app, lock_file_path)
    assert os.path.isfile(lock_file_path)


def test_lockfiledb_reads_existing_file(mock_app, lock_file_path):
    """Test LockFileDB reads existing lock file."""
    with open(lock_file_path, "w") as f:
        f.write("file1.txt\nfile2.txt\n")
    
    db = LockFileDB(mock_app, lock_file_path)
    assert "file1.txt" in db.DB
    assert "file2.txt" in db.DB


def test_lockfiledb_lock(mock_app, lock_file_path, tmp_path):
    """Test LockFileDB.lock() method."""
    db = LockFileDB(mock_app, lock_file_path)
    mock_app.lambdaenv.root = str(tmp_path)
    
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Path(mock_app, str(test_file))
    
    db.lock(path)
    relpath = path.relativepath()
    # Check in DB_NEWS (lock adds to DB_NEWS, not DB directly)
    assert any(relpath in item for item in db.DB_NEWS)


def test_lockfiledb_islocked(mock_app, lock_file_path, tmp_path):
    """Test LockFileDB.islocked() method."""
    db = LockFileDB(mock_app, lock_file_path)
    mock_app.lambdaenv.root = str(tmp_path)
    
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Path(mock_app, str(test_file))
    
    # Initially not locked
    assert not db.islocked(path)
    
    # Lock it and save, then check
    db.lock(path)
    db.stop()  # Save the lock file
    # Reload to read from file
    db2 = LockFileDB(mock_app, lock_file_path)
    assert db2.islocked(path)


def test_lockfiledb_unlock(mock_app, lock_file_path, tmp_path):
    """Test LockFileDB.unlock() method."""
    db = LockFileDB(mock_app, lock_file_path)
    mock_app.lambdaenv.root = str(tmp_path)
    
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    path = Path(mock_app, str(test_file))
    
    # Lock it first and save
    db.lock(path)
    db.stop()
    db2 = LockFileDB(mock_app, lock_file_path)
    assert db2.islocked(path)
    
    # Unlock it (unlock doesn't return a value, just modifies state)
    db2.unlock(path)
    assert not db2.islocked(path)
