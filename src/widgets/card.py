# card.py
#
# Copyright 2026 qewer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess
import os
from enum import Enum
from pathlib import Path

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib

from dataclasses import dataclass, field

from ..backend import WineBackend
from ..backend import ELFBackend

def get_binary_type(path) -> CardType:
    try:
        result = subprocess.run(
            ["file", path],
            capture_output=True,
            text=True,
            check=True,
        )

        output = result.stdout.lower()

        if "appimage" in output:
            return CardType.APPIMAGE
        elif "elf" in output:
            return CardType.ELF
        elif "pe32" in output or "ms-dos executable" in output:
            return CardType.EXE
        else:
            return CardType.OTHER

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"file command failed: {e.stderr}") from e

class CardType(str, Enum):
    EXE = "exe"
    ELF = "elf"
    APPIMAGE = "appimage"
    OTHER = "other"


@dataclass
class ZLibCardData:
    """Library card dataclass"""
    title: str
    icon: str
    path: str
    arguments: list[str] | None = None
    wine_prefix: Path = field(
        default_factory=lambda: (
            Path(GLib.get_user_data_dir())
            / "tr.org.pardus.zkutuphane"
            / "wineprefix"
        )
    )

    def __post_init__(self):
        self.type = get_binary_type(self.path) 
        self._wine = WineBackend(wine_prefix = self.wine_prefix)
        self._elf = ELFBackend()
    
    def run(self):
        if self.type ==  CardType.ELF or self.type == CardType.APPIMAGE:
            return self._elf.launch(
                executable = self.path
            )
        elif self.type == CardType.EXE:
            return self._wine.launch(
                executable=self.path,
                arguments=self.arguments,
            )

@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/card.ui")
class ZLibCard(Adw.Bin):
    """Library card widget element"""

    __gtype_name__ = "ZLibCard"

    card_icon = Gtk.Template.Child()
    card_title = Gtk.Template.Child()

    def __init__(self, data: ZLibCardData, **kwargs):
        super().__init__(**kwargs)

        self.data = data
        self.card_title.set_text(data.title)
        self.card_icon.set_from_icon_name(data.icon)


