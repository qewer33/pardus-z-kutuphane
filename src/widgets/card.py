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

from dataclasses import dataclass, field
from pathlib import Path

from gi.repository import Adw, Gio, GLib, Gtk

from ..backend.typedetector import ExecutableType


@dataclass
class ZLibCardData:
    """Library card dataclass"""

    title: str
    icon: str
    path: str
    type: ExecutableType
    publisher: str | None = None
    arguments: list[str] | None = None
    wine_prefix: Path = field(
        default_factory=lambda: (
            Path(GLib.get_user_data_dir()) / "tr.org.pardus.zkutuphane" / "wineprefix"
        )
    )
    running: bool = False
    log_buffer: Gtk.TextBuffer = field(default_factory=Gtk.TextBuffer)

    def to_dict(self) -> dict:
        """Serialize the persistent fields (skips transient runtime state)"""
        return {
            "title": self.title,
            "icon": self.icon,
            "path": self.path,
            "type": self.type.value,
            "publisher": self.publisher,
            "arguments": self.arguments,
            "wine_prefix": str(self.wine_prefix),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ZLibCardData":
        return cls(
            title=data["title"],
            icon=data["icon"],
            path=data["path"],
            type=ExecutableType(data["type"]),
            publisher=data.get("publisher"),
            arguments=data["arguments"],
            wine_prefix=Path(data["wine_prefix"]),
        )


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/card.ui")
class ZLibCard(Adw.Bin):
    """Library card widget element"""

    __gtype_name__ = "ZLibCard"

    card_icon = Gtk.Template.Child()
    card_title = Gtk.Template.Child()
    card_publisher = Gtk.Template.Child()

    def __init__(self, data: ZLibCardData, **kwargs):
        super().__init__(**kwargs)

        self.data = data
        self.card_title.set_text(data.title)
        self.card_icon.set_from_icon_name(data.icon)
        if data.publisher:
            self.card_publisher.set_text(data.publisher)
        else:
            self.card_publisher.set_visible(False)
