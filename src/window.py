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

import json
import os
import threading
from pathlib import Path
from urllib.parse import urlparse

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from .backend import ExecutableType, Launcher, PublisherDetector, TagDetector, TypeDetector
from .util.logger import get_logger
from .widgets import LogWindow, ZLibAddBookDialog, ZLibCardData, ZLibTypePill

logger = get_logger(os.path.basename(__file__))

SCHEMA_ID = "tr.org.pardus.zkutuphane"

LIBRARY_FILE = (
    Path(GLib.get_user_data_dir()) / "tr.org.pardus.zkutuphane" / "library.json"
)


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/window.ui")
class ZLibAppWindow(Adw.ApplicationWindow):
    """Main application window"""

    __gtype_name__ = "ZLibAppWindow"

    card_view = Gtk.Template.Child()
    card_stack = Gtk.Template.Child()
    card_action_bar = Gtk.Template.Child()
    card_selected_label = Gtk.Template.Child()
    pill_container = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # guards library auto-save while cards are being loaded from disk
        self._loading = False

        # type pill shown in the bottom bar for the selected card
        self.type_pill = ZLibTypePill()
        self.pill_container.append(self.type_pill)

        # remember window size across sessions
        self._bind_window_size()

        # setup drag & drop
        drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_file_drop)
        self.add_controller(drop_target)

        # setup card view actions
        self.card_view.connect("card-selected", self.on_card_selected)
        self.card_view.connect("library-changed", self.on_library_changed)

        for name, handler in (
            ("launch-card", self.on_launch_card),
            ("configure-card", self.on_configure_card),
            ("show-log-card", self.on_show_log_card),
            ("remove-card", self.on_remove_card),
            ("open-file", lambda a, p: self.on_open_folder_clicked(None)),
            ("add-link", lambda a, p: self.on_add_link_clicked(None)),
        ):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", handler)
            self.add_action(action)

        self._update_launch_action()

        self.load_library()

    def _bind_window_size(self) -> None:
        source = Gio.SettingsSchemaSource.get_default()
        if source is None or source.lookup(SCHEMA_ID, True) is None:
            logger.warning(
                "GSettings schema %s not found; window size won't persist", SCHEMA_ID
            )
            return
        settings = Gio.Settings(schema_id=SCHEMA_ID)
        settings.bind("width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT)

    # library persistence

    def load_library(self) -> None:
        if not LIBRARY_FILE.exists():
            return
        # suppress auto-save while populating from disk (nothing changed yet)
        self._loading = True
        for entry in json.loads(LIBRARY_FILE.read_text()):
            self.add_card(ZLibCardData.from_dict(entry))
        self._loading = False
        # clear selection
        GLib.idle_add(self._clear_card_selection)

    def _clear_card_selection(self) -> int:
        self.card_view.unselect_all()
        return GLib.SOURCE_REMOVE

    def on_library_changed(self, _view) -> None:
        if not self._loading:
            self.save_library()

    def save_library(self) -> None:
        LIBRARY_FILE.parent.mkdir(parents=True, exist_ok=True)
        cards = self.card_view.cards_data_list
        LIBRARY_FILE.write_text(json.dumps([card.to_dict() for card in cards]))

    # web book related handlers
    def on_add_link_clicked(self, _button: Gtk.Button):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Web Kitap Bağlantısı Ekle",
            body="Kitabın internet adresini girin:",
        )
        dialog.add_response("cancel", "İptal")
        dialog.add_response("add", "Ekle")
        dialog.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("cancel")

        entry = Gtk.Entry()
        entry.set_placeholder_text("https://")
        dialog.set_extra_child(entry)

        def on_response(dialog, response):
            if response == "add":
                url = entry.get_text().strip()
                if url:
                    if not url.startswith(("http://", "https://")):
                        url = "https://" + url
                    publisher = PublisherDetector.detect(url)
                    card_data = ZLibCardData(
                        title=urlparse(url).netloc or url,
                        icon="web-browser-symbolic",
                        path=url,
                        type=ExecutableType.WEBBOOK,
                        publisher=publisher,
                        tags=TagDetector.detect_from_publisher(publisher),
                    )
                    self._show_add_book_dialog(card_data)
            dialog.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    def on_open_folder_clicked(self, _button: Gtk.Button):
        try:
            dialog = Gtk.FileDialog()
            dialog.set_title("Bir Z-Kitap Uygulaması Seçin...")
            dialog.open(self, None, self.on_folder_chosen)
        except GLib.Error as e:
            logger.error("FileDialog error: %s %s %s", e.message, e.domain, e.code)
            return

    # file open signal handlers
    def on_folder_chosen(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        try:
            file = dialog.open_finish(result)
        except GLib.Error as e:
            # user dismiss
            if e.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED):
                return
            logger.error("FileDialog error: %s %s %s", e.message, e.domain, e.code)
            return
        if file is None:
            return

        card_data = self._card_from_file(file.get_path())
        self._show_add_book_dialog(card_data)

    def on_file_drop(self, drop_target, file_list, x, y):
        if not isinstance(file_list, Gdk.FileList):
            return

        files = list(file_list)
        for file in files:
            card_data = self._card_from_file(file.get_path())
            # don't show dialog for multiple files
            if len(files) == 1:
                self._show_add_book_dialog(card_data)
            else:
                self.add_card(card_data)

    def _card_from_file(self, path: str) -> ZLibCardData:
        type = TypeDetector.get_executable_type(path)
        publisher = PublisherDetector.detect(path)
        icon = "application-pdf" if type == ExecutableType.PDF else "dialog-question-symbolic"
        tags = TagDetector.detect_from_filename(path) or TagDetector.detect_from_publisher(publisher)
        return ZLibCardData(
            Path(path).stem, icon, path, type, publisher, tags
        )

    def _show_add_book_dialog(self, card_data: ZLibCardData) -> None:
        dialog = ZLibAddBookDialog(card_data, self.add_card)
        dialog.present(self)

    # card view signal handlers

    def add_card(self, card_data: ZLibCardData) -> None:
        self.card_view.add_card(card_data)
        self.card_stack.set_visible_child_name("cards")
        # save happens via the card view's "library-changed" signal

    def on_card_selected(self, _view, card_data):
        if card_data is None:
            self.card_action_bar.set_revealed(False)
            self._update_launch_action()
            return
        self.card_selected_label.set_text(card_data.title)
        self.type_pill.set_book_type(card_data.type)
        self.card_action_bar.queue_draw()
        self.card_action_bar.set_revealed(True)
        self._update_launch_action()

    def on_launch_card(self, _action, _param):
        card_data = self.card_view.get_selected_card()
        if card_data is None or card_data.running:
            return

        try:
            process = Launcher.launch(card_data)
        except Exception as e:
            logger.error("Launch failed for %s: %s", card_data.path, e)
            if isinstance(e, FileNotFoundError):
                body = f"Dosya bulunamadı:\n{card_data.path}"
            else:
                body = str(e)
            self._show_error(f"“{card_data.title}” başlatılamadı", body)
            return

        card_data.running = True
        card_data.log_buffer.set_text("")
        self._update_launch_action()

        def _wait():
            for line in process.stdout:
                GLib.idle_add(self._append_log, card_data, line)
            process.wait()
            card_data.running = False
            logger.info("App exited: %s", card_data.path)
            GLib.idle_add(self._update_launch_action)

        threading.Thread(target=_wait, daemon=True).start()

    def _append_log(self, card_data: ZLibCardData, line: str) -> int:
        buffer = card_data.log_buffer
        buffer.insert(buffer.get_end_iter(), line)
        return GLib.SOURCE_REMOVE

    def on_show_log_card(self, _action, _param):
        card_data = self.card_view.get_selected_card()
        if card_data is None:
            return
        log_window = LogWindow(card_data, transient_for=self)
        log_window.present()

    def _update_launch_action(self) -> None:
        """Enable the launch button only for a selected not running card"""
        selected = self.card_view.get_selected_card()
        if selected is not None:
            self.lookup_action("launch-card").set_enabled(not selected.running)

    def _show_error(self, heading: str, body: str) -> None:
        dialog = Adw.AlertDialog(heading=heading, body=body)
        dialog.add_response("ok", "Tamam")
        dialog.present(self)

    def on_configure_card(self, _action, _param):
        card_data = self.card_view.get_selected_card()
        if card_data is None:
            return
        dialog = ZLibAddBookDialog(
            card_data,
            self._on_card_configured,
            title="Kitabı Yapılandır",
            confirm_label="Tamam",
        )
        dialog.present(self)

    def _on_card_configured(self, card_data: ZLibCardData) -> None:
        self.card_view.refresh_selected_card()
        self.card_selected_label.set_text(card_data.title)
        self.save_library()

    def on_remove_card(self, _action, _param):
        # save happens via the card view's "library-changed" signal
        self.card_view.remove_selected_card()
        if not self.card_view.cards_data_list:
            self.card_stack.set_visible_child_name("empty")
