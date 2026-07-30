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
from gettext import gettext as _
from pathlib import Path
from urllib.parse import urlparse

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk

from .backend import (
    ALL_TAGS,
    ExecutableType,
    Launcher,
    PublisherDetector,
    TagDetector,
    TypeDetector,
)
from .util.csd_resize import enable_edge_resize
from .util.logger import get_logger
from .widgets import LogWindow, ZLibAddBookDialog, ZLibCardData
from .widgets.type_pill import pill_info

logger = get_logger(os.path.basename(__file__))

SCHEMA_ID = "tr.org.pardus.zkutuphane"

LIBRARY_FILE = (
    Path(GLib.get_user_data_dir()) / "tr.org.pardus.zkutuphane" / "library.json"
)

SUBJECT_FILTERS = [
    ("tum", "Tüm Dersler", "view-grid-symbolic", "#808080", set()),
    ("matematik", "Matematik", "accessories-calculator-symbolic", "#3498db", {"Matematik", "Geometri", "Problemler"}),
    ("turkce", "Türkçe", "accessories-dictionary-symbolic", "#e74c3c", {"Türkçe", "Türk Dili ve Edebiyatı", "Edebiyat", "Dil ve Anlatım", "Paragraf", "Dil Bilgisi"}),
    ("fen", "Fen", "applications-science-symbolic", "#2ecc71", {"Fen", "Fen Bilimleri", "Fizik", "Kimya", "Biyoloji"}),
    ("sosyal", "Sosyal", "system-users-symbolic", "#f39c12", {
        "Tarih", "İnkılap Tarihi", "Coğrafya", "Felsefe", "Psikoloji",
        "Sosyoloji", "Mantık", "Din Kültürü ve Ahlak Bilgisi",
        "Sosyal Bilgiler", "Vatandaşlık", "Demokrasi ve İnsan Hakları",
    }),
    ("yabanci", "Yabancı Dil", "preferences-desktop-locale-symbolic", "#9b59b6", {"İngilizce", "Almanca", "Fransızca", "Yabancı Dil"}),
    ("diger", "Diğer", "application-x-addon-symbolic", "#1abc9c", {
        "Hayat Bilgisi", "Rehberlik", "Sağlık Bilgisi", "Trafik ve İlk Yardım",
    }),
]


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/window.ui")
class ZLibAppWindow(Gtk.ApplicationWindow):
    """Main application window"""

    __gtype_name__ = "ZLibAppWindow"

    card_view = Gtk.Template.Child()
    card_stack = Gtk.Template.Child()
    card_action_bar = Gtk.Template.Child()
    card_selected_label = Gtk.Template.Child()
    tag_pill_container = Gtk.Template.Child()
    pill_container = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    search_publisher_btn = Gtk.Template.Child()
    search_tag_btn = Gtk.Template.Child()
    type_pill_icon = Gtk.Template.Child()
    type_pill_label = Gtk.Template.Child()
    publisher_filter_search = Gtk.Template.Child()
    publisher_filter_list = Gtk.Template.Child()
    tag_filter_search = Gtk.Template.Child()
    tag_filter_list = Gtk.Template.Child()
    subject_filter_box = Gtk.Template.Child()
    subject_scroll = Gtk.Template.Child()
    search_btn = Gtk.Template.Child()
    add_button = Gtk.Template.Child()
    hamburger = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.search_btn.bind_property(
            "active", self.search_bar, "search-mode-enabled",
            GObject.BindingFlags.BIDIRECTIONAL,
        )

        # We always draw our own window buttons (added below), so the header
        # bar's built-in window controls must never render. Disabling them
        # unconditionally is what prevents doubled buttons: relying on the
        # per-system decoration layout only worked where that layout happened
        # to be empty (e.g. Pardus etap) but doubled up on desktops whose
        # gtk-decoration-layout still lists min/max/close (e.g. XFCE/xfwm4).
        self.header_bar.set_show_title_buttons(False)

        # on Wayland CSD is native, so promote the header bar as titlebar.
        # on X11 (Pardus etap) Mutter ignores GDK decoration hints, so we use
        # set_decorated(False) with no set_titlebar() to avoid the hidden titlebox.
        is_x11 = self.get_display().__gtype__.name == "GdkX11Display"

        if is_x11:
            self.set_decorated(False)
            # undecorated X11 windows lose the WM resize border; restore it
            enable_edge_resize(self)
        else:
            box = self.get_child()
            if box is not None:
                box.remove(self.header_bar)
            self.set_titlebar(self.header_bar)

        # custom window buttons on the end side
        # pack_end prepends, so the last packed child is leftmost in the end_box
        # remove blueprint [end] children first so we can repack in the right order
        self.hamburger.unparent()
        self.search_btn.unparent()

        close_btn = self._make_title_button("window-close-symbolic", self.close)
        min_btn = self._make_title_button("window-minimize-symbolic", self.minimize)
        self._max_icon = Gtk.Image.new_from_icon_name("window-maximize-symbolic")
        self._max_btn = Gtk.Button()
        self._max_btn.set_child(self._max_icon)
        self._max_btn.add_css_class("titlebutton")
        self._max_btn.connect("clicked", lambda _: self._toggle_maximize())
        # pack in reverse order so the visual left-to-right is:
        # [search_btn] [hamburger] [min_btn] [max_btn] [close_btn]
        self.header_bar.pack_end(close_btn)        # rightmost
        self.header_bar.pack_end(self._max_btn)     # second from right
        self.header_bar.pack_end(min_btn)           # third from right
        self.header_bar.pack_end(self.hamburger)    # fourth from right
        self.header_bar.pack_end(self.search_btn)   # leftmost (closest to center)

        # double-click to maximize
        gesture = Gtk.GestureClick()
        gesture.set_button(1)
        gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        gesture.connect("pressed", self._on_header_double_click)
        self.header_bar.add_controller(gesture)
        self.connect("notify::maximized", self._on_maximized_changed)

        # TEMP: explicitly load libadwaita's own stylesheet so the app renders
        # as real Adwaita even when the system GTK theme (with an incomplete
        # gtk-4.0 port) would otherwise leave Adw widgets unstyled.
        #adw_provider = Gtk.CssProvider()
        #adw_provider.load_from_resource("/org/gnome/Adwaita/styles/gtk.css")
        #Gtk.StyleContext.add_provider_for_display(
        #    self.get_display(), adw_provider, Gtk.STYLE_PROVIDER_PRIORITY_THEME
        #)

        # TEMP: the incomplete system gtk-4.0 theme doesn't define the newer
        # accent named colors, so accent widgets fall back to white. Provide
        # the default Adwaita accent explicitly.
        #accent_css = (
        #    ":root { --accent-bg-color: #3584e4; --accent-fg-color: #ffffff; }"
        #)
        #accent_provider = Gtk.CssProvider()
        #accent_provider.load_from_string(accent_css)
        #Gtk.StyleContext.add_provider_for_display(
        #    self.get_display(), accent_provider, Gtk.STYLE_PROVIDER_PRIORITY_THEME + 1
        #)

        provider = Gtk.CssProvider()
        provider.load_from_resource("/tr/org/pardus/zkutuphane/style.css")
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # guards library auto-save while cards are being loaded from disk
        self._loading = False

        # remember window size across sessions
        self._bind_window_size()

        # setup drag & drop
        # Wayland (GTK 4.22+): DropTargetAsync + read_value_async(Gdk.FileList)
        # X11   (GTK 4.8):     DropTarget + G_TYPE_STRING, synchronous
        #                      text/uri-list delivery; assert warnings
        #                      are benign GTK 4.8 X11 bugs (#3755)
        if Gtk.get_minor_version() >= 10:
            formats = Gdk.ContentFormats.new_for_gtype(Gdk.FileList.__gtype__)
            drop_target = Gtk.DropTargetAsync.new(formats, Gdk.DragAction.COPY)
            drop_target.connect("accept", self._on_drop_accept)
            drop_target.connect("drop", self._on_drop_sync)
        else:
            drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING,
                                             Gdk.DragAction.COPY)
            drop_target.connect("accept", self._on_drop_accept)
            drop_target.connect("drop", self._on_drop_string)
        self.add_controller(drop_target)

        # setup search

        # shared filter state: the subject tiles and the tag filter list drive
        # the same underlying tag filter, so keep references to sync them
        self._syncing_filters = False
        self._tag_checkbuttons: dict[str, Gtk.CheckButton] = {}
        self._subject_buttons: dict[str, Gtk.ToggleButton] = {}
        self._subject_keywords: dict[str, set[str]] = {}

        self.search_bar.connect_entry(self.search_entry)
        self.search_bar.set_key_capture_widget(self)
        self.search_entry.connect("search-changed", self.on_search_changed)
        self._setup_filter_listbox(
            self.publisher_filter_list, self.publisher_filter_search,
            PublisherDetector.names(), self._on_publisher_filter,
        )
        self._setup_filter_listbox(
            self.tag_filter_list, self.tag_filter_search,
            ALL_TAGS, self._on_tag_filter, store=self._tag_checkbuttons,
        )
        self.search_bar.connect(
            "notify::search-mode-enabled", self.on_search_mode_changed
        )

        # subject filter buttons
        for slug, label, icon_name, color, keywords in SUBJECT_FILTERS:
            btn = Gtk.ToggleButton()
            box = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(18)
            lbl = Gtk.Label(label=label)
            box.append(icon)
            box.append(lbl)
            btn.set_child(box)
            btn.add_css_class("subject-filter-btn")
            btn.add_css_class(f"subject-{slug}")
            btn.connect("toggled", self._on_subject_filter)
            self.subject_filter_box.append(btn)
            self._subject_buttons[slug] = btn
            self._subject_keywords[slug] = set(keywords)

        # let a normal vertical wheel scroll the subject row horizontally
        scroll_ctrl = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.BOTH_AXES
        )
        scroll_ctrl.connect("scroll", self._on_subject_scroll)
        self.subject_scroll.add_controller(scroll_ctrl)

        # Tüm Dersler active by default (no subject filter)
        self._subject_buttons["tum"].set_active(True)

        # disable bell
        settings = Gtk.Settings.get_default()
        if settings is not None:
            settings.set_property("gtk-error-bell", False)

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
        self._update_log_action()

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

    # search

    def on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self.card_view.set_search_text(entry.get_text())

    def _setup_filter_listbox(
        self, listbox: Gtk.ListBox, search: Gtk.SearchEntry,
        items: list[str], on_change, store: dict | None = None,
    ) -> None:
        checkbuttons: list[Gtk.CheckButton] = []
        for item in items:
            cb = Gtk.CheckButton(label=item)
            listbox.append(cb)
            checkbuttons.append(cb)
            if store is not None:
                store[item] = cb

        def _update_filter(*_):
            selected = {cb.get_label() for cb in checkbuttons if cb.get_active()}
            on_change(selected)

        def _on_search(*_):
            text = search.get_text().strip().lower()
            for cb in checkbuttons:
                cb.set_visible(not text or text in cb.get_label().lower())

        search.connect("search-changed", _on_search)
        for cb in checkbuttons:
            cb.connect("toggled", _update_filter)

    def _on_publisher_filter(self, selected: set[str]) -> None:
        self.card_view.set_search_publishers(selected)

    def _on_tag_filter(self, selected: set[str]) -> None:
        # driven programmatically by a subject tile; it already filters
        if self._syncing_filters:
            return
        self.card_view.set_search_tags(selected)
        self._sync_subjects_from_tags(selected)

    def _apply_tags_to_checkboxes(self, tags: set[str]) -> None:
        """Check exactly the given tags in the tag filter list."""
        for label, cb in self._tag_checkbuttons.items():
            cb.set_active(label in tags)

    def _sync_subjects_from_tags(self, selected: set[str]) -> None:
        """Light up the subject tile matching the selected tags, if any."""
        match_slug = None
        if not selected:
            match_slug = "tum"
        else:
            for slug, keywords in self._subject_keywords.items():
                if slug != "tum" and keywords == selected:
                    match_slug = slug
                    break
        self._syncing_filters = True
        try:
            for slug, btn in self._subject_buttons.items():
                btn.set_active(slug == match_slug)
        finally:
            self._syncing_filters = False

    def _on_subject_scroll(self, _controller, dx: float, dy: float) -> bool:
        hadj = self.subject_scroll.get_hadjustment()
        if hadj is None:
            return False
        # translate a vertical (or horizontal) wheel notch into a horizontal step
        delta = dy if abs(dy) >= abs(dx) else dx
        if delta == 0:
            return False
        hadj.set_value(hadj.get_value() + delta * 50)
        return True

    def _on_subject_filter(self, btn) -> None:
        # the tiles act like radio buttons: one active subject at a time
        if self._syncing_filters:
            return
        self._syncing_filters = True
        try:
            clicked_slug = next(
                (s for s, b in self._subject_buttons.items() if b is btn), None
            )
            tum_btn = self._subject_buttons["tum"]

            if clicked_slug == "tum":
                # "Tüm Dersler" is the no-filter state; keep it the only active tile
                for slug, b in self._subject_buttons.items():
                    b.set_active(slug == "tum")
                keywords: set[str] = set()
            elif btn.get_active():
                # activate this subject, deactivate everything else (incl. Tüm Dersler)
                for b in self._subject_buttons.values():
                    if b is not btn:
                        b.set_active(False)
                keywords = set(self._subject_keywords.get(clicked_slug, set()))
            else:
                # toggled the active subject back off -> fall back to "Tüm Dersler"
                tum_btn.set_active(True)
                keywords = set()

            # keep the search-bar tag filters in sync, then filter once
            self._apply_tags_to_checkboxes(keywords)
            self.card_view.set_search_tags(keywords)
        finally:
            self._syncing_filters = False

    def on_search_mode_changed(self, search_bar, _param) -> None:
        if not search_bar.get_search_mode():
            self.search_entry.set_text("")
            self.publisher_filter_search.set_text("")
            self.tag_filter_search.set_text("")
            self._syncing_filters = True
            try:
                self._clear_filter_listbox(self.publisher_filter_list)
                self._clear_filter_listbox(self.tag_filter_list)
                for slug, btn in self._subject_buttons.items():
                    btn.set_active(slug == "tum")
            finally:
                self._syncing_filters = False
            self.card_view.set_search_publishers(set())
            self.card_view.set_search_tags(set())

    @staticmethod
    def _clear_filter_listbox(listbox: Gtk.ListBox) -> None:
        child = listbox.get_first_child()
        while child:
            if isinstance(child, Gtk.CheckButton):
                child.set_active(False)
            child = child.get_next_sibling()

    def _update_type_pill(self, book_type) -> None:
        label, icon, css_class = pill_info(book_type)
        self.type_pill_icon.set_from_resource(icon)
        self.type_pill_label.set_label(label)
        for cls in ("type-app", "type-web", "type-pdf"):
            self.pill_container.remove_css_class(cls)
        self.pill_container.add_css_class(css_class)

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
        logger.info("on_open_folder_clicked called (gtk=%s.%s)", Gtk.get_major_version(), Gtk.get_minor_version())
        try:
            if Gtk.get_major_version() >= 4 and Gtk.get_minor_version() >= 10:
                self._open_file_async()
            else:
                self._open_file_native()
        except Exception as e:
            logger.error("on_open_folder_clicked error: %s", e, exc_info=True)
            import traceback
            traceback.print_exc()

    def _open_file_async(self):
        try:
            dialog = Gtk.FileDialog()
            dialog.set_title("Bir Z-Kitap Uygulaması Seçin...")
            dialog.open(self, None, self._on_file_chosen_async)
        except GLib.Error as e:
            logger.error("FileDialog error: %s %s %s", e.message, e.domain, e.code)
            return

    def _on_file_chosen_async(self, dialog, result):
        try:
            file = dialog.open_finish(result)
        except GLib.Error as e:
            if e.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED):
                return
            logger.error("FileDialog error: %s %s %s", e.message, e.domain, e.code)
            return
        if file is None:
            return

        card_data = self._card_from_file(file.get_path())
        self._show_add_book_dialog(card_data)

    def _open_file_native(self):
        logger.info("Opening Gtk.FileChooserNative...")
        try:
            self._file_dialog = Gtk.FileChooserNative.new(
                "Bir Z-Kitap Uygulaması Seçin...",
                self,
                Gtk.FileChooserAction.OPEN,
                None, None,
            )
            self._file_dialog.connect("response", self._on_file_chosen_native)
            self._file_dialog.show()
        except Exception as e:
            logger.error("FileChooserNative error: %s", e)

    def _on_file_chosen_native(self, dialog, response):
        logger.info("FileChooserNative response: %s", response)
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file is not None:
                card_data = self._card_from_file(file.get_path())
                self._show_add_book_dialog(card_data)
        dialog.destroy()
        self._file_dialog = None

    def _on_drop_accept(self, target, drop):
        return True

    def _on_drop_sync(self, target, drop, x, y):
        drop.read_value_async(Gdk.FileList.__gtype__,
                              GLib.PRIORITY_DEFAULT, None,
                              self._on_drop_file_read, None)
        drop.finish(Gdk.DragAction.COPY)
        return True

    def _on_drop_file_read(self, drop, result, user_data):
        try:
            flist = drop.read_value_finish(result)
        except GLib.GError:
            return
        if flist is None:
            return
        try:
            files = list(flist)
        except TypeError:
            files = self._extract_files_ctypes(flist) or []
        if files:
            for file in files:
                card_data = self._card_from_file(file.get_path())
                if len(files) == 1:
                    self._show_add_book_dialog(card_data)
                else:
                    self.add_card(card_data)

    def _on_drop_string(self, target, value, x, y):
        text = value.get_string() if isinstance(value, GObject.Value) else value
        if not text:
            return False
        files = []
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                files.append(Gio.File.new_for_uri(line))
        if files:
            for file in files:
                card_data = self._card_from_file(file.get_path())
                if len(files) == 1:
                    self._show_add_book_dialog(card_data)
                else:
                    self.add_card(card_data)
        return True

    @staticmethod
    def _extract_files_ctypes(flist):
        import re, ctypes
        try:
            m = re.search(r"GdkFileList at (0x[0-9a-f]+)", repr(flist))
            if not m:
                return None
            addr = int(m.group(1), 16)
            slist_ptr = ctypes.cast(addr, ctypes.POINTER(ctypes.c_void_p))[0]
            if not slist_ptr:
                return None

            libgio = ctypes.CDLL("libgio-2.0.so")
            libgio.g_file_get_path.argtypes = [ctypes.c_void_p]
            libgio.g_file_get_path.restype = ctypes.c_char_p
            libgio.g_free.argtypes = [ctypes.c_void_p]
            libgio.g_free.restype = None

            files = []
            while slist_ptr:
                fields = ctypes.cast(slist_ptr, ctypes.POINTER(ctypes.c_void_p * 2))[0]
                gfile_ptr, next_ptr = fields[0], fields[1]
                if gfile_ptr:
                    path_ptr = libgio.g_file_get_path(gfile_ptr)
                    if path_ptr:
                        path = ctypes.cast(path_ptr, ctypes.c_char_p).value
                        if path:
                            files.append(Gio.File.new_for_path(path))
                        libgio.g_free(path_ptr)
                slist_ptr = next_ptr
            return files
        except Exception:
            return None

    def _card_from_file(self, path: str) -> ZLibCardData:
        type = TypeDetector.get_executable_type(path)
        publisher = PublisherDetector.detect(path)
        icon = (
            "application-pdf"
            if type == ExecutableType.PDF
            else "dialog-question-symbolic"
        )
        tags = TagDetector.detect_from_filename(
            path
        ) or TagDetector.detect_from_publisher(publisher)
        return ZLibCardData(Path(path).stem, icon, path, type, publisher, tags)

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
            self._update_log_action()
            return
        self.card_selected_label.set_text(card_data.title)
        self._update_type_pill(card_data.type)
        self._build_tag_pills(card_data.tags or [])
        self.card_action_bar.queue_draw()
        self.card_action_bar.set_revealed(True)
        self._update_launch_action()
        self._update_log_action()

    def on_launch_card(self, _action, _param):
        card_data = self.card_view.get_selected_card()
        if card_data is None or card_data.running:
            return

        # use the current global wine prefix from GSettings, so Preferences
        # changes take effect immediately on next launch
        try:
            val = Gio.Settings(schema_id="tr.org.pardus.zkutuphane").get_string("wine-prefix")
            if val:
                card_data.wine_prefix = Path(val).expanduser()
        except Exception:
            pass

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
        card_data.launch_count += 1
        self.card_view.invalidate_sort()
        self.save_library()
        card_data.log_buffer.set_text("")
        self._update_launch_action()

        def _wait():
            for raw in process.stdout:
                line = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
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

    def _update_log_action(self) -> None:
        """Enable the log ("Günce") menu item only for application types,
        since PDFs and web books don't produce a run log."""
        selected = self.card_view.get_selected_card()
        enabled = selected is not None and selected.type not in (
            ExecutableType.PDF,
            ExecutableType.WEBBOOK,
        )
        self.lookup_action("show-log-card").set_enabled(enabled)

    def _build_tag_pills(self, tags: list[str]) -> None:
        child = self.tag_pill_container.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.tag_pill_container.remove(child)
            child = nxt

        max_pills = 5
        visible = tags[:max_pills]
        extra = tags[max_pills:]

        for tag in visible:
            label = Gtk.Label(label=tag)
            label.set_css_classes(["tag-pill"])
            self.tag_pill_container.append(label)

        if extra:
            label = Gtk.Label(label=f"+{len(extra)}")
            label.set_css_classes(["tag-pill"])
            label.set_tooltip_text(", ".join(extra))
            self.tag_pill_container.append(label)

    def _show_error(self, heading: str, body: str) -> None:
        if hasattr(Adw, "AlertDialog"):
            dialog = Adw.AlertDialog(heading=heading, body=body)
            dialog.add_response("ok", "Tamam")
            dialog.present(self)
        else:
            dialog = Adw.MessageDialog(transient_for=self, heading=heading, body=body)
            dialog.add_response("ok", "Tamam")
            dialog.present()

    def on_configure_card(self, _action, _param):
        card_data = self.card_view.get_selected_card()
        if card_data is None:
            return
        dialog = ZLibAddBookDialog(
            card_data,
            self._on_card_configured,
            title="Kitabı Düzenle",
            confirm_label="Tamam",
        )
        dialog.present(self)

    def _on_card_configured(self, card_data: ZLibCardData) -> None:
        self.card_view.refresh_selected_card()
        self.card_selected_label.set_text(card_data.title)
        self._update_type_pill(card_data.type)
        self._build_tag_pills(card_data.tags or [])
        self._update_log_action()
        self.save_library()

    def on_remove_card(self, _action, _param):
        # save happens via the card view's "library-changed" signal
        self.card_view.remove_selected_card()
        if not self.card_view.cards_data_list:
            self.card_stack.set_visible_child_name("empty")

    @staticmethod
    def _make_title_button(icon_name, callback):
        btn = Gtk.Button.new_from_icon_name(icon_name)
        btn.add_css_class("titlebutton")
        btn.connect("clicked", lambda _: callback())
        return btn

    def _on_header_double_click(self, gesture, n_press, x, y):
        if n_press == 2:
            self._toggle_maximize()

    def _toggle_maximize(self):
        if self.is_maximized():
            self.unmaximize()
        else:
            self.maximize()

    def _on_maximized_changed(self, *args):
        icon = Gtk.Image.new_from_icon_name(
            "window-restore-symbolic" if self.is_maximized() else "window-maximize-symbolic",
        )
        self._max_btn.set_child(icon)
