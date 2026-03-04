"""
Custom library for lambda expressions.
These functions are automatically imported into the 'm' module.
"""

import subprocess as sp
import hashlib
from . import rulelexer
import types
import collections
import tempfile
import os
import sys
import logging
import unicodedata

try:
    from pypinyin import lazy_pinyin  # no tones by default
    CN_CONVERT = lambda x: " ".join(lazy_pinyin(x))
except ImportError:
    CN_CONVERT = lambda x: x

try:
    import pykakasi
    _kks = pykakasi.kakasi()
    JP_CONVERT = lambda x: " ".join([t.get("hepburn", "") for t in _kks.convert(x)])
except ImportError:
    JP_CONVERT = lambda x: x

try:
    from korean_romanizer.romanizer import Romanizer
    KR_CONVERT = lambda x: Romanizer(x).romanize()
except ImportError:
    KR_CONVERT = lambda x: x


# Unicode ranges (common enough for filenames)
R_HANGUL = [(0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F)]  # syllables + jamo
R_HIRAGANA = [(0x3040, 0x309F)]
R_KATAKANA = [(0x30A0, 0x30FF), (0x31F0, 0x31FF)]  # incl. phonetic extensions
R_HAN = [(0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF)]     # Ext A, Unified, Compat


def _has_any(s: str, ranges) -> bool:
    for ch in s:
        o = ord(ch)
        for a, b in ranges:
            if a <= o <= b:
                return True
    return False


def detect_scripts(text: str) -> set[str]:
    if not text:
        return set()

    scripts = set()
    if _has_any(text, R_HANGUL):
        scripts.add("kr")
    if _has_any(text, R_HIRAGANA) or _has_any(text, R_KATAKANA):
        scripts.add("jp")
    if _has_any(text, R_HAN):
        scripts.add("han")

    # "han" is a category, not a language; we’ll interpret below.
    return scripts


def detect_language_bucket(text: str) -> str:
    s = detect_scripts(text)
    if not s:
        return "other"

    # Mixed cases
    if "kr" in s and ("jp" in s or "han" in s):
        return "mixed"
    if "jp" in s and "kr" in s:
        return "mixed"

    if "kr" in s:
        return "kr"
    if "jp" in s:
        return "jp"
    if "han" in s:
        return "cn"   # “Han-only” defaulting to CN
    return "other"


class CustomException(Exception):
    pass


def guardexecution(func):
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except CustomException:
            # just pass CustomException since they are native to the wrapped commands
            raise
        except Exception:
            raise CustomException("Inline command threw exception").with_traceback(
                sys.exc_info()[2]
            )

    return wrapper


@guardexecution
def system(*args, **kw):
    """
    spawn a command and return status as boolean.
    """
    return sp.Popen(args, **kw).wait() == 0


def execute(*args, **kw):
    """
    spawn a command and return output or raise exception on status != 0 or empty output
    """
    kw["stdout"] = sp.PIPE

    # spawn
    proc = sp.Popen(args, **kw)

    # I/O
    data = proc.stdout.read()
    proc.stdout.close()

    # only return data on returncode == 0
    if proc.wait() != 0:
        raise CustomException("Command returned non-zero status code: " + repr(args))

    if data is None or data == "":
        raise CustomException("Command returned notthing on stdout: " + repr(args))

    return data


@guardexecution
def filter(data, *args, **kw):
    """
    spawn a command and return value as boolean.
    """
    if data is None:
        return ""

    kw["stdin"] = sp.PIPE
    kw["stdout"] = sp.PIPE

    # spawn
    proc = sp.Popen(args, **kw)

    # I/O
    proc.stdin.write(data.encode("utf-8"))
    proc.stdin.close()
    data = proc.stdout.read()
    proc.stdout.close()

    # only return data on returncode == 0
    if proc.wait() != 0:
        raise CustomException("Command returned non-zero status code")

    if data is None or data == "":
        raise CustomException("Command returned notthing on stdout")
    if proc.wait() != 0:
        raise CustomException("Command returned non-zero status code: " + repr(args))

    if data is None or data == "":
        raise CustomException("Command returned notthing on stdout: " + repr(args))

    return data


@guardexecution
def md5sum(target):
    if target is None:
        return None

    with open(target, "rb") as f:
        return hashlib.md5(f.read()).digest()


@guardexecution
def foreign(text):
    if text is None:
        return None

    if not isinstance(text, str):
        if isinstance(text, (bytes, bytearray)):
            d_text = text.decode("utf-8", errors="replace")
        else:
            d_text = str(text)
    else:
        d_text = text

    scripts = detect_scripts(d_text)

    # Korean first if Hangul present
    if "kr" in scripts:
        d_text = KR_CONVERT(d_text)

    # Japanese only if kana present (this avoids CN -> JP kanji readings)
    if "jp" in scripts:
        d_text = JP_CONVERT(d_text)

    # Chinese only if Han present AND no kana (i.e. Han-only or Han+Latin/etc.)
    if "han" in scripts and "jp" not in scripts:
        d_text = CN_CONVERT(d_text)

    return d_text


@guardexecution
def ue(text):
    """
    Do not allow _any_ unicode characters to pass by here.
    """
    if text is None:
        return None

    if type(text) != str:
        d_text = str(text).deocde("utf-8")
    else:
        d_text = text

    buildstr = []

    for c in d_text:
        if ord(c) > 127:
            buildstr.append(f"{ord(c):02X}")
        else:
            buildstr.append(c)

    return "".join(buildstr)


cached_books = {}


@guardexecution
def lexer(rb, string):
    global cached_books

    if not os.path.isfile(rb):
        raise CustomException("Rulebook does not exist: " + rb)

    if rb in cached_books:
        return cached_books[rb].match(string)

    lexer = rulelexer.RuleLexer()
    with open(rb, "r", encoding="utf-8") as f:
        lexer.lex(rulelexer.FileReader(f))

    if len(lexer.errors) > 0:
        for error in lexer.errors:
            (line, col), message = error
            logging.warning(rb + ":" + str(line) + ":" + str(col) + " " + message)

    cached_books[rb] = rulelexer.RuleBook(lexer)
    return cached_books[rb].match(string)


@guardexecution
def inspect(o):
    print("inspection:", type(o), repr(o))
    return o


@guardexecution
def case(mv, *args, **kw):
    """
    Match a value against a set of cases.

    The following matchmethods are available:

    case('foo', bar="result1", foo="result2") -> "result"
    case('foo', ('bar', "result1"), ('foo', "result2")) -> "result2"
    case('foo', (('bar', 'baz'), "result1"), (('foo', 'biz'), "result2")) -> "result2"

    The match does not have to be a string:

    case(2, (1, "result1"), (2, "result2")) -> "result2"
    """
    for a in args:
        if not isinstance(a, tuple) and len(a) != 2:
            continue

        kv, v = a

        if isinstance(kv, collections.Sequence):
            if mv in kv:
                return v
        elif mv == kv:
            return v

    # match a kw
    return kw.get(str(mv), None)


@guardexecution
def each(*args):
    """
    Run each argument if a FunctionType, in successive order.
    Stop running on the first function to return false.
    """
    for a in args:
        if type(a) != types.FunctionType:
            continue

        if not a():
            return False

    return True


@guardexecution
def in_tmp(func, *args, **kw):
    """
    Create a temporary file, use it as the first argument to a function, transparently also pass the other arguments.

    empty function: in_tmp(lambda tmp: ... )
    Function with arguments: in_tmp(lambda tmp, foo: ... , "foo")
    """
    if type(func) != types.FunctionType:
        return None

    fo, tmp = tempfile.mkstemp()
    os.close(fo)

    try:
        return func(tmp, *args, **kw)
    finally:
        os.unlink(tmp)


__all__ = ["ue", "case", "inspect", "each", "in_tmp"]
