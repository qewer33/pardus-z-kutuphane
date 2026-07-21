# log_window.py
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

from gi.repository import Adw, Gtk

from .card import ZLibCardData


class LogWindow(Adw.Window):
    """Window showing the live log output of the launched card"""

    def __init__(self, card_data: ZLibCardData, **kwargs):
        super().__init__(**kwargs)

        self.set_title(f"Günce: {card_data.title}")
        self.set_default_size(700, 450)

        text_view = Gtk.TextView(buffer=card_data.log_buffer)
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.set_monospace(True)

        scrolled = Gtk.ScrolledWindow(child=text_view, vexpand=True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(Adw.HeaderBar())
        box.append(scrolled)

        self.set_content(box)
