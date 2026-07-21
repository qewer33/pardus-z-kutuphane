import os
from pathlib import Path

from gi.repository import Adw, Gio, GLib, Gtk

from ..backend.wine import WineBackend

SCHEMA_ID = "tr.org.pardus.zkutuphane"


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/preferences_dialog.ui")
class PreferencesDialog(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesDialog"

    genel_page = Gtk.Template.Child()
    wine_page = Gtk.Template.Child()
    _sort_switch = Gtk.Template.Child()
    _log_dir_row = Gtk.Template.Child()
    _log_dir_browse = Gtk.Template.Child()
    _cache_dir_row = Gtk.Template.Child()
    _cache_dir_browse = Gtk.Template.Child()
    _wine_prefix_row = Gtk.Template.Child()
    _wine_prefix_browse = Gtk.Template.Child()
    _winecfg_btn = Gtk.Template.Child()
    _regedit_btn = Gtk.Template.Child()
    _wineboot_btn = Gtk.Template.Child()
    _open_prefix_btn = Gtk.Template.Child()

    def present(self, parent=None):
        if parent is not None:
            self.set_transient_for(parent)
        super().present()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._file_dialog = None

        self._settings = Gio.Settings(schema_id=SCHEMA_ID)

        self._settings.bind(
            "sort-by-launch-count", self._sort_switch, "active", Gio.SettingsBindFlags.DEFAULT
        )
        self._settings.bind(
            "wine-prefix", self._wine_prefix_row, "text", Gio.SettingsBindFlags.DEFAULT
        )
        self._settings.bind(
            "log-dir", self._log_dir_row, "text", Gio.SettingsBindFlags.DEFAULT
        )
        self._settings.bind(
            "cache-dir", self._cache_dir_row, "text", Gio.SettingsBindFlags.DEFAULT
        )

        self._wine_prefix_browse.connect("clicked", self._on_browse, self._wine_prefix_row)
        self._log_dir_browse.connect("clicked", self._on_browse, self._log_dir_row)
        self._cache_dir_browse.connect("clicked", self._on_browse, self._cache_dir_row)

        self._winecfg_btn.connect("clicked", self._on_winecfg)
        self._regedit_btn.connect("clicked", self._on_regedit)
        self._wineboot_btn.connect("clicked", self._on_wineboot)
        self._open_prefix_btn.connect("clicked", self._on_open_prefix)

        if not WineBackend.is_installed():
            for btn in (self._winecfg_btn, self._regedit_btn, self._wineboot_btn, self._open_prefix_btn):
                btn.set_sensitive(False)
                btn.set_tooltip_text("Wine sistemde bulunamadı")

        try:
            self.genel_page.props.icon_name = "preferences-system-symbolic"
        except AttributeError:
            pass
        try:
            self.wine_page.props.icon_name = "computer-symbolic"
        except AttributeError:
            pass

    def _prefix(self) -> str:
        return Path(self._settings.get_string("wine-prefix")).expanduser()

    def _on_winecfg(self, _btn: Gtk.Button) -> None:
        WineBackend.winecfg(wine_prefix=self._prefix())

    def _on_regedit(self, _btn: Gtk.Button) -> None:
        WineBackend.run_command("regedit", wine_prefix=self._prefix())

    def _on_wineboot(self, _btn: Gtk.Button) -> None:
        WineBackend.run_command("wineboot", "-r", wine_prefix=self._prefix())

    def _on_open_prefix(self, _btn: Gtk.Button) -> None:
        path = self._prefix()
        path.mkdir(parents=True, exist_ok=True)
        Gio.AppInfo.launch_default_for_uri(
            Gio.File.new_for_path(str(path)).get_uri()
        )

    def _on_browse(self, button: Gtk.Button, row: Adw.EntryRow) -> None:
        if Gtk.get_major_version() >= 4 and Gtk.get_minor_version() >= 10:
            self._browse_async(button, row)
        else:
            self._browse_native(button, row)

    def _browse_async(self, button: Gtk.Button, row: Adw.EntryRow) -> None:
        folder_dialog = Gtk.FileDialog.new()
        initial = Path(row.get_text()).expanduser()
        if initial.exists():
            folder_dialog.set_initial_folder(Gio.File.new_for_path(str(initial)))
        folder_dialog.select_folder(
            self.get_root(), None, lambda d, r: self._on_folder_selected(d, r, row)
        )

    def _on_folder_selected(
        self, dialog, result: Gio.AsyncResult, row: Adw.EntryRow
    ) -> None:
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        if folder is not None:
            row.set_text(folder.get_path())

    def _browse_native(self, button: Gtk.Button, row: Adw.EntryRow) -> None:
        dialog = Gtk.FileChooserNative.new(
            "Dizin Seç", self, Gtk.FileChooserAction.SELECT_FOLDER
        )
        initial = Path(row.get_text()).expanduser()
        if initial.exists():
            dialog.set_current_folder(Gio.File.new_for_path(str(initial)))
        dialog.connect("response", self._on_chooser_response, row)
        self._file_dialog = dialog
        dialog.show()

    def _on_chooser_response(self, dialog, response, row) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            folder = dialog.get_file()
            if folder is not None:
                row.set_text(folder.get_path())
        dialog.destroy()
        self._file_dialog = None
