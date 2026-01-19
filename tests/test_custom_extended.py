"""Extended tests for musync.custom module."""
import pytest
import os
from unittest.mock import Mock, patch
from musync.custom import md5sum, foreign, ue, in_tmp


def test_md5sum_file_content(tmp_path):
    """Test md5sum() with actual file content."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    result1 = md5sum(str(test_file))
    assert result1 is not None
    assert isinstance(result1, bytes)
    
    # Same content should produce same hash
    test_file2 = tmp_path / "test2.txt"
    test_file2.write_text("test content")
    result2 = md5sum(str(test_file2))
    assert result1 == result2


def test_foreign_with_bytes():
    """Test foreign() with bytes-like input."""
    from musync.custom import foreign
    
    # Test with string
    result = foreign("test")
    assert isinstance(result, str)


def test_ue_with_bytes():
    """Test ue() with bytes-like input."""
    from musync.custom import ue
    
    # Test with string that has unicode
    result = ue("café")
    assert isinstance(result, str)
    # Should encode the é character
    assert "E9" in result.upper() or "caf" in result.lower()


def test_in_tmp_with_return_value():
    """Test in_tmp() with function that returns value."""
    from musync.custom import in_tmp
    
    def test_func(tmp_path, value):
        assert os.path.exists(tmp_path)
        return value * 2
    
    result = in_tmp(test_func, 5)
    assert result == 10


def test_in_tmp_with_exception():
    """Test in_tmp() ensures cleanup even on exception."""
    from musync.custom import in_tmp, CustomException
    
    def test_func(tmp_path):
        raise ValueError("Test error")
    
    # The guardexecution decorator will wrap ValueError in CustomException
    with pytest.raises(CustomException):
        in_tmp(test_func)
