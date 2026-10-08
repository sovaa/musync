import os
from typing import Any


def _positive_int(value: Any) -> int | None:
    """First positive integer in a numeric tag. Zero and blank mean unknown."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value > 0 else None

    text = str(value).strip()
    if not text:
        return None
    try:
        number = int(text)
    except ValueError:
        return None
    return number if number > 0 else None


def parse_disc_pair(value: Any) -> tuple[int | None, int | None]:
    """Disc number and total from '1', '1/2', 1, (1, 2), or [1, 2]."""
    if isinstance(value, str):
        parts = value.split("/", 1)
        disc = _positive_int(parts[0])
        total = _positive_int(parts[1]) if len(parts) > 1 else None
        return disc, total
    if isinstance(value, (list, tuple)):
        disc = _positive_int(value[0]) if len(value) > 0 else None
        total = _positive_int(value[1]) if len(value) > 1 else None
        return disc, total
    return _positive_int(value), None


def normalize_disc(meta: "MetaFile") -> None:
    """Store disc and disctotal as positive ints, or None when absent.

    An explicit disctotal tag wins over a total embedded in the disc number
    ('1/2'). A stored total of 0 is treated as unknown.
    """
    disc, total_from_number = parse_disc_pair(meta.disc)
    total = _positive_int(meta.disctotal)
    if total is None:
        total = total_from_number
    meta.disc = disc
    meta.disctotal = total


class MetaFile:
    __translate__: Any = None

    def __init__(self, f: Any, tags: dict[str, list[Any]]) -> None:
        self.album = None
        self.artist = None
        self.title = None
        self.track = None
        self.year = None
        self.disc = None
        self.disctotal = None
        self.filename = os.path.basename(f.filename)

        idx = self.filename.rfind(".")

        if idx > 0:
            self.ext = self.filename[idx + 1 :].lower()

        if self.__translate__:
            for key in list(self.__translate__.keys()):
                ukey = key.upper()

                for tagkey in list(tags.keys()):
                    if ukey != tagkey.upper():
                        continue

                    attr = self.__translate__[key]

                    if getattr(self, attr) is not None:
                        continue

                    setattr(self, attr, tags[tagkey][0])

        normalize_disc(self)
