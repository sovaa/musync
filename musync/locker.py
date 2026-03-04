#
# Copyright (C) 2007 Albin Stjerna, John-John Tedro
#
#    This file is part of Musync.
#
#    Musync is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Musync is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Musync.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

import string
from pathlib import Path as PathLib
from typing import Any

from musync.commons import Path


class LockFileDB:
    def __init__(self, app: Any, lock_path: str) -> None:
        self.app = app
        self.changed = False
        self.removed = False
        self.lock_path = lock_path

        if not PathLib(self.lock_path).is_file():
            with open(self.lock_path, "w", encoding="utf-8") as f:
                pass

        with open(self.lock_path, "r", encoding="utf-8") as f:
            self.DB = [x.strip(string.whitespace) for x in f.readlines()]

        self.DB_NEWS = []

    def unlock(self, path: Path) -> bool:
        if not self.islocked(path):
            self.app.notice("is not locked:", path.path)
            return False

        if not path.inroot():
            self.app.warning("is not in root:", path.path)
            return False

        self.DB.remove(path.relativepath())
        self.changed = True
        self.removed = True

    def lock(self, path: Path) -> bool:
        if self.islocked(path):
            self.app.notice("is already locked:", path.path)
            return False

        if self.parentislocked(path):
            self.app.notice("is already locked (parent):", path.path)
            return False

        if not path.inroot():
            self.app.warning("is not in root:", path.path)
            return False

        self.DB_NEWS.append(path.relativepath() + "\n")
        self.changed = True

    def islocked(self, path: Path) -> bool:
        return path.relativepath() in self.DB

    def parentislocked(self, path: Path) -> bool:
        return path.parent().relativepath() in self.DB

    def stop(self) -> None:
        if self.changed:
            # this will trigger writing if database has been changed.
            if not PathLib(self.lock_path).is_file():
                with open(self.lock_path, "w", encoding="utf-8") as f:
                    pass

            if self.removed:
                with open(self.lock_path, "w", encoding="utf-8") as f:
                    for p in self.DB:
                        f.writelines(p)
                    f.write("\n")
            else:
                with open(self.lock_path, "a", encoding="utf-8") as f:
                    f.writelines(self.DB_NEWS)
