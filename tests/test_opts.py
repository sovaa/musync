"""Tests for musync.opts module."""
import os
import pytest
from configparser import RawConfigParser
from unittest.mock import Mock, patch, MagicMock
import musync.opts
from musync.opts import LambdaEnviron, LambdaTemplate, AppSession, Usage, cfgfiles



class TestLambdaEnviron:
    """Tests for LambdaEnviron."""

    def test_setattr_stores_item(self):
        le = LambdaEnviron({})
        le.foo = "bar"
        assert le["foo"] == "bar"

    def test_getattr_existing_key(self):
        le = LambdaEnviron({"a": 1})
        assert le.a == 1

    def test_getattr_missing_key_raises(self):
        le = LambdaEnviron({})
        with pytest.raises(Exception) as exc_info:
            _ = le.missingkey
        assert "No such key" in str(exc_info.value)
        assert "missingkey" in str(exc_info.value)

    def test_hasattr_existing(self):
        le = LambdaEnviron({"x": 1})
        assert le.__hasattr__("x") is True

    def test_hasattr_missing(self):
        le = LambdaEnviron({})
        assert le.__hasattr__("y") is False


class TestAppSessionOverlayImport:
    """Tests for AppSession.overlay_import."""

    def test_no_import_section_returns_false(self):
        session = Mock()
        session.printer = Mock()
        session.imports = {}
        session.lambdaenv = {}
        parser = RawConfigParser()
        parser.add_section("general")
        result = musync.opts.AppSession.overlay_import(session, parser)
        assert result is False
        session.printer.error.assert_called_once()
        assert "import" in str(session.printer.error.call_args)

    def test_empty_key_warns_and_continues(self):
        session = Mock()
        session.printer = Mock()
        session.imports = {}
        session.lambdaenv = {}
        parser = RawConfigParser()
        parser.add_section("import")
        parser.set("import", "emptykey", "")
        result = musync.opts.AppSession.overlay_import(session, parser)
        session.printer.warning.assert_called_once()
        assert result is True

    def test_successful_import(self):
        session = Mock()
        session.printer = Mock()
        session.imports = {}
        session.lambdaenv = {}
        parser = RawConfigParser()
        parser.add_section("import")
        parser.set("import", "os_module", "os")
        result = musync.opts.AppSession.overlay_import(session, parser)
        assert result is True
        assert "os_module" in session.lambdaenv
        assert session.lambdaenv["os_module"] is os

    def test_import_error_returns_false(self):
        session = Mock()
        session.printer = Mock()
        session.imports = {}
        session.lambdaenv = {}
        parser = RawConfigParser()
        parser.add_section("import")
        parser.set("import", "bad", "nonexistent_module_xyz_123")
        result = musync.opts.AppSession.overlay_import(session, parser)
        assert result is False
        session.printer.error.assert_called()


class TestAppSessionOverlaySettings:
    """Tests for AppSession.overlay_settings."""

    def test_missing_section_returns_false(self):
        session = Mock()
        session.printer = Mock()
        session.settings = {}
        session.lambdaenv = {}
        parser = RawConfigParser()
        parser.add_section("other")
        result = musync.opts.AppSession.overlay_settings(session, parser, "missing")
        assert result is False
        session.printer.error.assert_called_once()

    def test_empty_key_warns_and_continues(self):
        session = Mock()
        session.printer = Mock()
        session.settings = {}
        session.lambdaenv = {}
        parser = RawConfigParser()
        parser.add_section("sect")
        parser.set("sect", "emptykey", "")
        result = musync.opts.AppSession.overlay_settings(session, parser, "sect")
        session.printer.warning.assert_called_once()
        assert result is True

    def test_eval_success(self):
        session = Mock()
        session.printer = Mock()
        session.settings = {}
        session.lambdaenv = {}
        parser = RawConfigParser()
        parser.add_section("sect")
        parser.set("sect", "root", '"/tmp/music"')
        result = musync.opts.AppSession.overlay_settings(session, parser, "sect")
        assert result is True
        assert session.lambdaenv["root"] == "/tmp/music"

    def test_eval_exception_returns_false(self):
        session = Mock()
        session.printer = Mock()
        session.settings = {}
        session.lambdaenv = {}
        parser = RawConfigParser()
        parser.add_section("sect")
        parser.set("sect", "bad", "1 + syntax error (")
        result = musync.opts.AppSession.overlay_settings(session, parser, "sect")
        assert result is False
        session.printer.error.assert_called()


class TestParseWithClick:
    """Tests for AppSession._parse_with_click."""

    def test_short_flag_pretend(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["-p", "add", "file"])
        assert ("-p", "") in opts
        assert args == ["add", "file"]

    def test_long_flag_recursive(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["-R", "add"])
        assert ("-R", "") in opts or ("--recursive", "") in opts
        assert "add" in args

    def test_root_with_value(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["--root", "/music", "add"])
        assert ("--root", "/music") in opts

    def test_config_short_with_value(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["-c", "section", "add"])
        assert ("-c", "section") in opts or ("--config", "section") in opts

    def test_operation_and_files(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["add", "a.mp3", "b.mp3"])
        assert args == ["add", "a.mp3", "b.mp3"]

    def test_long_opt_equals_value(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["--root", "/path", "add"])
        assert any(r == "/path" for _, r in opts)

    def test_option_after_operation(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["add", "file.mp3", "-v"])
        assert "add" in args
        assert "file.mp3" in args
        assert ("-v", "") in opts or ("--verbose", "") in opts

    def test_modify_option(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["-M", "artist=Test", "add"])
        assert any(opt in ("-M", "--modify") and val == "artist=Test" for opt, val in opts)

    def test_multiple_options_after_operation(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(
            session, ["add", "f1.mp3", "f2.mp3", "-p", "-v", "--force"]
        )
        assert args[:3] == ["add", "f1.mp3", "f2.mp3"]
        assert ("-p", "") in opts
        assert ("-f", "") in opts or ("--force", "") in opts

    def test_short_opts_combined(self):
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["-pRv", "add"])
        assert "add" in args
        assert any("-p" in opt or "-R" in opt or "-v" in opt for opt, _ in opts)

    def test_unknown_long_opt_treated_as_operation(self):
        """Unknown long option is treated as start of operation (args)."""
        session = Mock()
        opts, args = musync.opts.AppSession._parse_with_click(session, ["--unknown", "add", "file"])
        assert "add" in args
        assert "file" in args


class TestReadArgv:
    """Tests for AppSession.read_argv."""

    def test_no_config_file_returns_none(self):
        session = Mock()
        session.printer = Mock()
        session.overlay_import = Mock()
        session.overlay_settings = Mock()
        session._parse_with_click = Mock()
        with patch("musync.opts.cfgfiles", [["nonexistent", "path", "config.conf"]]):
            with patch("os.path.isfile", return_value=False):
                result = musync.opts.AppSession.read_argv(session, [])
        assert result == (None, None, None)
        session.printer.error.assert_called()
        session.overlay_import.assert_not_called()

    def test_with_config_calls_overlay_and_parse(self, tmp_path):
        cfg = tmp_path / "musync.conf"
        cfg.write_text(
            "[import]\n"
            "os = os\n"
            "[general]\n"
            "root = \"/tmp\"\n"
            "targetpath = \"lambda x: 'a'\"\n"
            "add = \"lambda a,b: None\"\n"
            "rm = \"lambda x: None\"\n"
            "hash = \"lambda p: ''\"\n"
            "checkhash = False\n"
        )
        session = Mock()
        session.printer = Mock()
        session.overlay_import = Mock(return_value=True)
        session.overlay_settings = Mock(return_value=True)
        session._parse_with_click = Mock(return_value=([], ["help"]))
        with patch("musync.opts.cfgfiles", [[str(tmp_path), "musync.conf"]]):
            result = musync.opts.AppSession.read_argv(session, ["help"])
        assert result[0] is not None
        session.overlay_import.assert_called_once()
        session.overlay_settings.assert_called()
        session._parse_with_click.assert_called_once()


class TestUsage:
    """Tests for Usage and help generation."""

    def test_usage_returns_string(self):
        text = Usage()
        assert isinstance(text, str)
        assert "musync" in text.lower() or "option" in text.lower()