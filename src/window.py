# window.py
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
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib

from .widgets import ZLibCardData


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/window.ui")
class ZLibAppWindow(Adw.ApplicationWindow):
    """Main application window"""

    __gtype_name__ = "ZLibAppWindow"

    card_view = Gtk.Template.Child()
    card_stack = Gtk.Template.Child()
    open_folder = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.open_folder.connect("clicked", self.on_open_folder_clicked)

        # setup drag & drop target
        drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_file_drop)
        self.add_controller(drop_target)

    def on_open_folder_clicked(self, _button: Gtk.Button):
        dialog = Gtk.FileDialog()
        dialog.set_title("Bir Z-Kitap Uygulaması Seçin...")
        dialog.open(self, None, self.on_folder_chosen)

    def on_folder_chosen(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return
        if file is None:
            return

        card_data = ZLibCardData(file.get_basename(), "dialog-question-symbolic")
        self.add_card(card_data)

    def on_file_drop(self, drop_target, file_list, x, y):
        if isinstance(file_list, Gdk.FileList):
            for file in file_list:
                card_data = ZLibCardData(
                    file.get_basename(), "dialog-question-symbolic"
                )
                self.add_card(card_data)

    def add_card(self, card_data: ZLibCardData) -> None:
        self.card_view.add_card(card_data)
        self.card_stack.set_visible_child_name("cards")

