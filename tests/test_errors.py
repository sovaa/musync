"""Tests for musync.errors module."""
import pytest
from musync.errors import WarningException, FatalException


def test_warning_exception():
    """Test WarningException creation and message."""
    exc = WarningException("Test warning")
    assert str(exc) == "Test warning"
    assert isinstance(exc, Exception)


def test_fatal_exception():
    """Test FatalException creation and message."""
    exc = FatalException("Test fatal error")
    assert str(exc) == "Test fatal error"
    assert isinstance(exc, Exception)


def test_exception_inheritance():
    """Test that exceptions inherit from Exception."""
    assert issubclass(WarningException, Exception)
    assert issubclass(FatalException, Exception)
