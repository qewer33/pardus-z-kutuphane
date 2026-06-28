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

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib

from dataclasses import dataclass


@dataclass
class ZLibCardData:
    """Library card dataclass"""

    title: str
    icon: str


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/card.ui")
class ZLibCard(Gtk.Button):
    """Library card widget element"""

    __gtype_name__ = "ZLibCard"

    card_icon = Gtk.Template.Child()
    card_title = Gtk.Template.Child()

    def __init__(self, data: ZLibCardData, **kwargs):
        super().__init__(**kwargs)

        self.card_title.set_text(data.title)
        self.card_icon.set_from_icon_name(data.icon)

