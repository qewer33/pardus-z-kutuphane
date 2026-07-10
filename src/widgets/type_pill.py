# type_pill.py
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

from gi.repository import Gtk

from ..backend.typedetector import ExecutableType

# book type -> (label, symbolic icon, css class). Linux and Windows apps are
# intentionally merged into a single "Uygulama" category; anything unrecognized
# also falls back to it.
_WEB = ("Web", "internet-web-browser-symbolic", "type-web")
_PDF = ("PDF", "emblem-documents-symbolic", "type-pdf")
_APP = ("Uygulama", "applications-all-symbolic", "type-app")


def pill_info(book_type: ExecutableType) -> tuple[str, str, str]:
    if book_type == ExecutableType.WEBBOOK:
        return _WEB
    if book_type == ExecutableType.PDF:
        return _PDF
    return _APP


def type_icon(book_type: ExecutableType) -> str:
    """Symbolic icon name for a book type (same icon used by the pill)."""
    return pill_info(book_type)[1]


# book cover image tinted per category (defaults to the app/green cover)
_BOOK_RESOURCES = {
    ExecutableType.WEBBOOK: "book-blue.png",
    ExecutableType.PDF: "book-red.png",
}


def book_resource(book_type: ExecutableType) -> str:
    name = _BOOK_RESOURCES.get(book_type, "book-green.png")
    return f"/tr/org/pardus/zkutuphane/resources/{name}"


class ZLibTypePill(Gtk.Box):
    """Small colored pill showing a book's type (icon + label)"""

    def __init__(self):
        super().__init__(spacing=5)
        self.add_css_class("type-pill")

        self._icon = Gtk.Image()
        self._icon.set_pixel_size(14)
        self._label = Gtk.Label()
        self.append(self._icon)
        self.append(self._label)

        self._current_class = None

    def set_book_type(self, book_type: ExecutableType) -> None:
        label, icon, css_class = pill_info(book_type)
        self._icon.set_from_icon_name(icon)
        self._label.set_label(label)

        if self._current_class:
            self.remove_css_class(self._current_class)
        self.add_css_class(css_class)
        self._current_class = css_class
