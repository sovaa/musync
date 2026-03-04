import os
from typing import Any


class MetaFile:
    __translate__: Any = None

    def __init__(self, f: Any, tags: dict[str, list[Any]]) -> None:
        self.album = None
        self.artist = None
        self.title = None
        self.track = None
        self.year = None
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
