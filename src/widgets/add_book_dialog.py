# add_book_dialog.py
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

from ..backend.publisherdetector import PublisherDetector
from ..backend.typedetector import ExecutableType
from .card import UNKNOWN_PUBLISHER, ZLibCardData

# launch categories
_FILE_CATEGORIES = [
    ("Linux Uygulaması", ExecutableType.ELF),
    ("Windows Uygulaması", ExecutableType.PE64),
]
_WEB_CATEGORY = ("Web Kitabı", ExecutableType.WEBBOOK)

# detected type
_CATEGORY_INDEX = {
    ExecutableType.ELF: 0,
    ExecutableType.APPIMAGE_V1: 0,
    ExecutableType.APPIMAGE_V2: 0,
    ExecutableType.PE32: 1,
    ExecutableType.PE64: 1,
}


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/add_book_dialog.ui")
class ZLibAddBookDialog(Adw.Dialog):
    """Dialog to review a book's metadata before adding it to the library"""

    __gtype_name__ = "ZLibAddBookDialog"

    book_icon = Gtk.Template.Child()
    title_row = Gtk.Template.Child()
    publisher_row = Gtk.Template.Child()
    type_row = Gtk.Template.Child()
    cancel_button = Gtk.Template.Child()
    add_button = Gtk.Template.Child()

    def __init__(self, card_data: ZLibCardData, on_confirm, confirm_label="Ekle", **kwargs):
        super().__init__(**kwargs)

        self.card_data = card_data
        self.on_confirm = on_confirm
        self.is_web = card_data.type == ExecutableType.WEBBOOK

        self.add_button.set_label(confirm_label)
        self.book_icon.set_from_icon_name(card_data.icon)
        self.title_row.set_text(card_data.title)

        # publisher dropdown
        self._publishers = [UNKNOWN_PUBLISHER] + PublisherDetector.names()
        self.publisher_row.set_model(Gtk.StringList.new(self._publishers))
        if card_data.publisher in self._publishers:
            self.publisher_row.set_selected(self._publishers.index(card_data.publisher))

        # type dropdown, locked to Web for web books, else launch categories
        self._categories = [_WEB_CATEGORY] if self.is_web else _FILE_CATEGORIES
        labels = [label for label, _ in self._categories]
        self.type_row.set_model(Gtk.StringList.new(labels))
        if not self.is_web:
            self.type_row.set_selected(_CATEGORY_INDEX.get(card_data.type, 0))
        self.type_row.set_sensitive(not self.is_web)

        self.cancel_button.connect("clicked", lambda _button: self.close())
        self.add_button.connect("clicked", self._on_add)

    def _on_add(self, _button):
        card_data = self.card_data
        card_data.title = self.title_row.get_text().strip() or card_data.title

        publisher = self._publishers[self.publisher_row.get_selected()]
        card_data.publisher = None if publisher == UNKNOWN_PUBLISHER else publisher

        card_data.type = self._categories[self.type_row.get_selected()][1]

        self.close()
        self.on_confirm(card_data)
