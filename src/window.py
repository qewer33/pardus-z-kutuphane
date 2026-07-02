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

import os
from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib

from .widgets import ZLibCardData
from .util.logger import get_logger

logger = get_logger(os.path.basename(__file__))

@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/window.ui")
class ZLibAppWindow(Adw.ApplicationWindow):
    """Main application window"""

    __gtype_name__ = "ZLibAppWindow"

    card_view = Gtk.Template.Child()
    card_stack = Gtk.Template.Child()
    open_folder = Gtk.Template.Child()
    card_action_bar = Gtk.Template.Child()
    card_selected_label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # setup file open and drag & drop actions
        self.open_folder.connect("clicked", self.on_open_folder_clicked)

        drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_file_drop)
        self.add_controller(drop_target)

        # setup card view actions
        self.card_view.connect("card-selected", self.on_card_selected)
        
        for name, handler in (
            ("launch-card", self.on_launch_card),
            ("configure-card", self.on_configure_card),
        ):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", handler)
            self.add_action(action)

    # file open signal handlers

    def on_open_folder_clicked(self, _button: Gtk.Button):
        try:
            dialog = Gtk.FileDialog()
            dialog.set_title("Bir Z-Kitap Uygulaması Seçin...")
            dialog.open(self, None, self.on_folder_chosen)
        except GLib.Error:
            logger.error("FileDialog error:", e.message, e.domain, e.code)
            return

    def on_folder_chosen(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            logger.error("FileDialog error:", e.message, e.domain, e.code)
            return
        if file is None:
            return

        card_data = ZLibCardData(file.get_basename(), "dialog-question-symbolic", file.get_path())
        self.add_card(card_data)
        logger.info(f"Added card: {card_data.path}, Type:{card_data.type}")

    def on_file_drop(self, drop_target, file_list, x, y):
        if isinstance(file_list, Gdk.FileList):
            for file in file_list:
                card_data = ZLibCardData(
                    file.get_basename(), "dialog-question-symbolic", file.get_path()
                )
                self.add_card(card_data)
                logger.info(f"Added card: {card_data.path}, Type:{card_data.type}")

    # card view signal handlers

    def add_card(self, card_data: ZLibCardData) -> None:
        self.card_view.add_card(card_data)
        self.card_stack.set_visible_child_name("cards")

    def on_card_selected(self, _view, card_data):
        if card_data is None:
            self.card_action_bar.set_revealed(False)
            return
        self.card_selected_label.set_text(card_data.title)
        self.card_action_bar.set_revealed(True)

    def on_launch_card(self, _action, _param):
        card_data = self.card_view.get_selected_card()
        if card_data is None:
            return
        card_data.run()
        # TODO

    def on_configure_card(self, _action, _param):
        card_data = self.card_view.get_selected_card()
        # TODO

