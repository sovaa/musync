"""Tests for musync.rulelexer module."""
import pytest
import re
from unittest.mock import Mock
from musync.rulelexer import (
    Reader,
    StringReader,
    FileReader,
    RuleLexer,
    RuleBook,
)


class TestReader:
    """Tests for Reader base and StringReader/FileReader."""

    def test_string_reader_advance(self):
        r = StringReader("ab")
        assert next(r) == "a"
        assert next(r) == "b"
        assert next(r) is None
        assert r.empty()

    def test_string_reader_empty_pos_current(self):
        r = StringReader("x")
        assert not r.empty()
        assert r.pos() == 0
        assert r.current() is None
        next(r)
        assert r.current() == "x"
        assert r.pos() == 1
        next(r)
        assert r.current() is None
        assert r.empty()

    def test_string_reader_ignore(self):
        r = StringReader("ab", ignore=["a"])
        ch = next(r)
        assert ch == "b"
        assert r.current() == "b"
        next(r)
        assert r.empty()

    def test_string_reader_blank_returns_none(self):
        r = StringReader("")
        assert next(r) is None
        assert r.empty()

    def test_file_reader_chars(self, tmp_path):
        f = (tmp_path / "f.txt")
        f.write_text("xy")
        with open(f, "r", encoding="utf-8") as fp:
            r = FileReader(fp)
            assert next(r) == "x"
            assert next(r) == "y"
            assert next(r) is None
        assert r.empty()

    def test_file_reader_empty_file(self, tmp_path):
        f = (tmp_path / "empty.txt")
        f.write_text("")
        with open(f, "r", encoding="utf-8") as fp:
            r = FileReader(fp)
            assert next(r) is None
        assert r.empty()


class TestRuleLexerLexrule:
    """Tests for RuleLexer.lexrule."""

    def test_blank_line_returns_none_ok(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("")
        assert ok is None
        assert msg == "blank line"

    def test_whitespace_only_invalid_command(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("   ")
        assert ok is False
        assert "invalid" in msg

    def test_invalid_first_char(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("x_y_z")
        assert ok is False
        assert "invalid" in msg
        assert "x" in msg

    def test_unexpected_end_of_line(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("u")
        assert ok is False
        assert "unexpected end" in msg

    def test_unicode_single_codepoint(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("u_U+63_a_")
        assert ok is True
        assert msg is None
        assert len(lexer.tree) == 1
        cmd, rule, repl = lexer.tree[0]
        assert cmd == RuleLexer.UNICODE
        assert 0x63 in rule
        assert repl == "a"

    def test_unicode_range(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("u_U+63-U+64,U+65_a_")
        assert ok is True
        assert len(lexer.tree) == 1
        cmd, rule, repl = lexer.tree[0]
        assert (0x63, 0x64) in rule or 0x63 in rule
        assert repl == "a"

    def test_unicode_invalid_group(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("u_U+zz_a_")
        assert ok is False
        assert "could not match" in msg or "invalid" in msg

    def test_regexp_valid(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("s_/[a-z]+/_")
        assert ok is True
        assert len(lexer.tree) == 1
        cmd, rule, repl = lexer.tree[0]
        assert cmd == RuleLexer.REGEXP
        assert isinstance(rule, re.Pattern)
        assert repl == ""

    def test_regexp_invalid_compile(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("s_/[x_")
        assert ok is False
        assert "invalid" in msg

    def test_regexp_with_replacement(self):
        lexer = RuleLexer()
        ok, pos, msg = lexer.lexrule("s_foo_bar_")
        assert ok is True
        cmd, rule, repl = lexer.tree[0]
        assert repl == "bar"


class TestRuleLexerLex:
    """Tests for RuleLexer.lex (multi-line)."""

    def test_lex_single_line(self):
        lexer = RuleLexer()
        lexer.lex(StringReader("u_U+63_a_\n"))
        assert len(lexer.tree) == 1
        assert len(lexer.errors) == 0

    def test_lex_comment_ignored(self):
        lexer = RuleLexer()
        lexer.lex(StringReader("u_U+63_a_\n# comment\nu_U+64_b_\n"))
        assert len(lexer.tree) == 2
        assert len(lexer.errors) == 0

    def test_lex_blank_line_skipped(self):
        lexer = RuleLexer()
        lexer.lex(StringReader("u_U+63_a_\n\n\nu_U+64_b_\n"))
        assert len(lexer.tree) == 2

    def test_lex_error_accumulated(self):
        lexer = RuleLexer()
        lexer.lex(StringReader("u_U+63_a_\ninvalid\nu_U+64_b_\n"))
        assert len(lexer.tree) == 2
        assert len(lexer.errors) == 1
        (line, pos), message = lexer.errors[0]
        assert "invalid" in message or "command" in message


class TestRuleBook:
    """Tests for RuleBook and match."""

    def test_rulebook_unicode_match(self):
        lexer = RuleLexer()
        lexer.lexrule("u_U+63-U+64,U+65_a_")
        rb = RuleBook(lexer)
        assert rb.match("c") == "a"
        assert rb.match("d") == "a"
        assert rb.match("e") == "a"
        assert rb.match("x") == "x"

    def test_rulebook_regex_match(self):
        lexer = RuleLexer()
        lexer.lexrule("s_foo_bar_")
        rb = RuleBook(lexer)
        assert rb.match("foo") == "bar"
        assert rb.match("xfooy") == "xbary"

    def test_rulebook_char_then_string(self):
        lexer = RuleLexer()
        lexer.lexrule("u_U+63_a_")
        lexer.lexrule("s_a_b_")
        rb = RuleBook(lexer)
        assert rb.match("c") == "b"

    def test_rulebook_empty_string(self):
        lexer = RuleLexer()
        rb = RuleBook(lexer)
        assert rb.match("") == ""
