# -*- encoding: utf-8 -*-

from __future__ import annotations

import re
from typing import Any


class Reader:
    def __init__(self, ignore: list[str] | None = None) -> None:
        self._current = None
        self._ignore = [] if ignore is None else ignore
        self._pos = 0
        self._empty = False

    def __next__(self) -> str | None:
        if self.empty():
            return None

        while True:
            self._current = self._get_next()

            if self._current is None:
                self._empty = True
                break

            self._pos += 1

            if self._current in self._ignore:
                continue

            break

        return self._current

    def empty(self) -> bool:
        return self._empty

    def pos(self) -> int:
        return self._pos

    def current(self) -> str | None:
        return self._current


class StringReader(Reader):
    def __init__(self, string: str, **kw: Any) -> None:
        Reader.__init__(self, **kw)
        self._iterstring = iter(string)

    def _get_next(self) -> str | None:
        try:
            return next(self._iterstring)
        except StopIteration:
            return None


class FileReader(Reader):
    def __init__(self, fileobject: Any, **kw: Any) -> None:
        Reader.__init__(self, **kw)
        self._fileobject = fileobject

    def _get_next(self) -> str | None:
        r = self._fileobject.read(1)

        if r is None or r == "":
            return None

        return r


class RuleLexer:
    """
    This is a fake lexer/parser to handle the simple syntax for unicode rule replacement.
    """

    REGEXP = "s"
    UNICODE = "u"

    COMMANDS = [REGEXP, UNICODE]

    unicode_token = re.compile(r"^U?\+?([A-Fa-f0-9]+)$")
    unicodegroup_token = re.compile(r"^U?\+?([A-Fa-f0-9]+)-U?\+?([A-Fa-f0-9]+)$")

    def __init__(self) -> None:
        self.tree = []
        self.errors = []
        self._line = 0

    def lex(self, reader: Reader) -> None:
        while not reader.empty():
            line = []

            while next(reader) != "\n":
                if reader.current() is None:
                    break

                if reader.current() == "#":
                    while next(reader) != "\n":
                        pass
                    break

                line.append(reader.current())

            self._line += 1

            ok, pos, message = self.lexrule("".join(line).strip())

            if ok is None:
                continue

            if not ok:
                self.errors.append(((self._line, pos), message))

    def lexrule(
        self, line: str | None = None
    ) -> tuple[bool | None, int, str | None]:
        reader = StringReader(line)

        # check first character
        if next(reader) not in self.COMMANDS:
            if reader.current() is None:
                return (None, -1, "blank line")
            else:
                return (
                    False,
                    reader.pos(),
                    "invalid syntax: '" + reader.current() + "' is not a valid command",
                )

        command = reader.current()

        if next(reader) is None:
            return (False, reader.pos(), "invalid syntax: unexpected end of line")

        sep = reader.current()

        rule = []
        while next(reader) != sep:
            if reader.current() is None:
                return (
                    False,
                    reader.pos(),
                    "invalid syntax: expected separator '" + sep + "'",
                )
            rule.append(reader.current())

        rule = "".join(rule)

        if command == self.UNICODE:
            groups = rule.split(",")
            rule = []

            for i, group in enumerate(groups):
                group = group.strip()

                if group == "":
                    # no harm in silently ignoring this
                    continue

                m = self.unicode_token.match(group)
                if m is not None:
                    rule.append(int(m.group(1), 16))
                    continue

                m = self.unicodegroup_token.match(group)
                if m is not None:
                    rule.append((int(m.group(1), 16), int(m.group(2), 16)))
                    continue

                return (
                    False,
                    reader.pos(),
                    "invalid syntax: could not match rule number " + str(i),
                )
        elif command == self.REGEXP:
            try:
                rule = re.compile(rule)
            except Exception as e:
                return (False, reader.pos(), "invalid syntax: " + str(e))

        repl = []
        while next(reader) != sep:
            # implicit end
            if reader.current() is None:
                break

            repl.append(reader.current())

        self.tree.append((command, rule, "".join(repl)))
        return (True, -1, None)


class RuleBook:
    def __init__(self, lexer: RuleLexer, **kw: Any) -> None:
        self.kw = kw

        self.lexer = lexer
        self.charrules = []
        self.chardict = {}
        self.stringrules = []

        def create_unicoderule(ruleset, to_c):
            res = {}
            for rule in ruleset:
                if type(rule) == int:
                    res[rule] = to_c
                else:
                    fromc, toc = rule
                    for i in range(fromc, toc + 1):
                        res[i] = to_c
            return res

        for rule in lexer.tree:
            if rule[0] == RuleLexer.REGEXP:
                self.stringrules.append((rule[1], rule[2]))
            elif rule[0] == RuleLexer.UNICODE:
                self.chardict.update(create_unicoderule(rule[1], rule[2]))

    def match(self, string: str) -> list[str]:
        res = []

        for c in string:
            res.append(self.chardict.get(ord(c), c))

        # string pass;
        string = "".join(res)

        for regex, repl in self.stringrules:
            string = regex.sub(repl, string)

        return string


if __name__ == "__main__":
    import sys

    lexer = RuleLexer()
    assert lexer.lexrule("u_U+63-U+64,U+65_a_") == (True, -1, None)
    rulebook = RuleBook(lexer)
    print(lexer.tree)
    # print rulebook.rules[0].root.group[1].matchc
    print(rulebook.match("cest"))
    sys.exit(0)

    print(lexer.tree)

    lexer2 = RuleLexer()
    lexer2.lex(
        StringReader(
            """
s_U+30_å_
r/_/_/
  """
        )
    )

    print(lexer2.tree)
    print(lexer2.errors)

    lexer3 = RuleLexer()
    with open("test.txt", "r", encoding="utf-8") as f:
        lexer3.lex(FileReader(f))

    rulebook = RuleBook(lexer3)
    print(rulebook.match("testeGÅ"))
