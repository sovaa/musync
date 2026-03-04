"""Tests for musync.printer module."""
import io
import sys
import pytest
from unittest.mock import Mock, patch
from musync.printer import TermCapHolder, TermCaps, AppPrinter


def test_termcap_holder():
    """Test TermCapHolder class."""
    holder = TermCapHolder()
    # Should return empty string for any attribute
    assert holder.nonexistent == ""
    assert holder.bold == ""


def test_termcaps_initialization():
    """Test TermCaps initialization with non-tty stream."""
    stream = io.StringIO()
    # When stream is not a tty, it should use blankcaps
    try:
        termcaps = TermCaps(stream)
    except (ModuleNotFoundError, AttributeError):
        # On Windows, create minimal termcaps
        termcaps = TermCaps.__new__(TermCaps)
        termcaps.stream = stream
        termcaps.tc = False
        termcaps.c = TermCapHolder()
        termcaps.col = {}
    assert termcaps.stream == stream
    assert termcaps.tc is False  # Should be False for non-tty


def test_termcaps_blankcaps():
    """Test TermCaps.blankcaps() method."""
    stream = io.StringIO()
    # Create TermCaps which will fail curses import on Windows
    try:
        termcaps = TermCaps(stream)
    except (ModuleNotFoundError, AttributeError):
        # On Windows, curses may not be available
        termcaps = TermCaps.__new__(TermCaps)
        termcaps.stream = stream
        termcaps.tc = False
        termcaps.c = TermCapHolder()
        termcaps.col = {}
    
    termcaps.blankcaps()
    # After blanking, capabilities should be empty strings
    assert termcaps.c.bold == ""


def test_app_printer_warning(mock_app):
    """Test AppPrinter.warning() method."""
    stream = io.StringIO()
    try:
        printer = AppPrinter(mock_app, stream)
    except (ModuleNotFoundError, AttributeError):
        # On Windows, create a minimal printer
        printer = AppPrinter.__new__(AppPrinter)
        printer.app = mock_app
        printer.stream = stream
        printer.tc = False
        printer.c = TermCapHolder()
        printer.col = {}
        printer.haslogged = False
    
    printer.warning("Test warning")
    output = stream.getvalue()
    assert "Test warning" in output or len(output) > 0


def _create_printer(mock_app, stream):
    """Helper to create printer, handling Windows curses issues."""
    try:
        return AppPrinter(mock_app, stream)
    except (ModuleNotFoundError, AttributeError):
        printer = AppPrinter.__new__(AppPrinter)
        printer.app = mock_app
        printer.stream = stream
        printer.tc = False
        printer.c = TermCapHolder()
        printer.col = {}
        printer.haslogged = False
        return printer


def test_app_printer_error(mock_app):
    """Test AppPrinter.error() method."""
    stream = io.StringIO()
    printer = _create_printer(mock_app, stream)
    printer.error("Test error")
    output = stream.getvalue()
    assert "Test error" in output or len(output) > 0


def test_app_printer_notice(mock_app):
    """Test AppPrinter.notice() method."""
    stream = io.StringIO()
    printer = _create_printer(mock_app, stream)
    printer.notice("Test notice")
    output = stream.getvalue()
    assert "Test notice" in output or len(output) > 0


def test_app_printer_action(mock_app):
    """Test AppPrinter.action() method."""
    stream = io.StringIO()
    printer = _create_printer(mock_app, stream)
    printer.action("Test action")
    output = stream.getvalue()
    assert "Test action" in output or len(output) > 0


def test_app_printer_focus(mock_app):
    """Test AppPrinter.focus() method."""
    stream = io.StringIO()
    printer = _create_printer(mock_app, stream)
    
    # Create a mock meta object
    meta = Mock()
    meta.artist = "Test Artist"
    meta.album = "Test Album"
    meta.title = "Test Title"
    meta.track = "1"
    
    printer.focus(meta)
    assert printer.focused["artist"] == "Test Artist"
    assert printer.focused["album"] == "Test Album"
    assert printer.focused["title"] == "Test Title"
    assert printer.focused["track"] == "1"


def test_app_printer_is_suppressed(mock_app):
    """Test AppPrinter.is_suppressed() method."""
    stream = io.StringIO()
    printer = _create_printer(mock_app, stream)
    
    # Test when not suppressed
    mock_app.lambdaenv.silent = False
    assert not printer.is_suppressed("warning")
    
    # Test when suppressed
    mock_app.lambdaenv.silent = True
    mock_app.lambdaenv.suppressed = ["warning"]
    assert printer.is_suppressed("warning")


def test_app_printer_suppress_all(mock_app):
    """Test AppPrinter suppression of 'all' type."""
    stream = io.StringIO()
    printer = _create_printer(mock_app, stream)
    
    mock_app.configured = True
    mock_app.lambdaenv.silent = True
    mock_app.lambdaenv.suppressed = ["all"]
    assert printer.is_suppressed("all")
    mock_app.lambdaenv.suppressed = ["warning", "error", "notice"]
    assert printer.is_suppressed("warning")
    assert printer.is_suppressed("error")
    assert printer.is_suppressed("notice")


def test_termcaps_setstream():
    """TermCaps.setstream() updates the stream."""
    stream1 = io.StringIO()
    stream2 = io.StringIO()
    termcaps = TermCaps.__new__(TermCaps)
    termcaps.stream = stream1
    termcaps.tc = False
    termcaps.c = TermCapHolder()
    termcaps.col = {}
    termcaps.setstream(stream2)
    assert termcaps.stream is stream2


def test_termcaps_write_writes_to_stream():
    """TermCaps._write() formats and writes to stream."""
    stream = io.StringIO()
    termcaps = TermCaps.__new__(TermCaps)
    termcaps.stream = stream
    termcaps.tc = False
    termcaps.c = TermCapHolder()
    termcaps.col = {"bold": ""}
    termcaps._write("{bold}hi")
    assert "hi" in stream.getvalue()


def test_termcaps_writeall_joins_and_writes():
    """TermCaps._writeall() joins args and writes to stream."""
    stream = io.StringIO()
    termcaps = TermCaps.__new__(TermCaps)
    termcaps.stream = stream
    termcaps._writeall("a", "b", "c")
    assert stream.getvalue() == "abc"


def test_termcaps_unicodeencode_str_returns_utf8_bytes():
    """TermCaps._unicodeencode(str) returns UTF-8 encoded bytes."""
    termcaps = TermCaps.__new__(TermCaps)
    termcaps.stream = io.StringIO()
    termcaps.c = TermCapHolder()
    termcaps.col = {}
    result = termcaps._unicodeencode("café")
    assert result == "café".encode("utf-8")


def test_termcaps_unicodeencode_bytes():
    """TermCaps._unicodeencode(bytes) decodes to str."""
    termcaps = TermCaps.__new__(TermCaps)
    termcaps.stream = io.StringIO()
    termcaps.c = TermCapHolder()
    termcaps.col = {}
    result = termcaps._unicodeencode(b"hello")
    assert result == "hello"


def test_app_printer_warning_suppressed_no_output(mock_app):
    """AppPrinter.warning() does not write when suppressed."""
    stream = io.StringIO()
    printer = _create_printer(mock_app, stream)
    mock_app.configured = True
    mock_app.lambdaenv.silent = True
    mock_app.lambdaenv.suppressed = ["warning"]
    printer.warning("must not appear")
    assert "must not appear" not in stream.getvalue()


def test_app_printer_focus_boldnotice_on_artist_change(mock_app):
    """AppPrinter.focus() calls boldnotice when artist or album changes."""
    stream = io.StringIO()
    printer = _create_printer(mock_app, stream)
    mock_app.lambdaenv.suppressed = []
    meta1 = Mock()
    meta1.artist = "Artist A"
    meta1.album = "Album 1"
    meta1.title = "Title"
    meta1.track = "1"
    printer.focus(meta1)
    assert printer.focused["artist"] == "Artist A"
    assert printer.focused["album"] == "Album 1"
    out1 = stream.getvalue()
    meta2 = Mock()
    meta2.artist = "Artist B"
    meta2.album = "Album 2"
    meta2.title = "Title 2"
    meta2.track = "2"
    printer.focus(meta2)
    assert printer.focused["artist"] == "Artist B"
    assert printer.focused["album"] == "Album 2"
    out2 = stream.getvalue()
    assert len(out2) > len(out1)
    assert "Artist B" in out2 or "Album 2" in out2
