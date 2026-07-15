import os
from pathlib import Path

from gi.repository import Adw, Gio, GLib, Gtk

from ..backend.wine import WineBackend

SCHEMA_ID = "tr.org.pardus.zkutuphane"


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/preferences_dialog.ui")
class PreferencesDialog(Adw.PreferencesDialog):

    __gtype_name__ = "PreferencesDialog"

    wine_prefix_row = Gtk.Template.Child()
    log_dir_row = Gtk.Template.Child()
    cache_dir_row = Gtk.Template.Child()
    wine_prefix_browse = Gtk.Template.Child()
    log_dir_browse = Gtk.Template.Child()
    cache_dir_browse = Gtk.Template.Child()
    winecfg_btn = Gtk.Template.Child()
    regedit_btn = Gtk.Template.Child()
    wineboot_btn = Gtk.Template.Child()
    open_prefix_btn = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # load GSettings and bind preferences rows
        self._settings = Gio.Settings(schema_id=SCHEMA_ID)

        self._settings.bind(
            "wine-prefix", self.wine_prefix_row, "text", Gio.SettingsBindFlags.DEFAULT
        )
        self._settings.bind(
            "log-dir", self.log_dir_row, "text", Gio.SettingsBindFlags.DEFAULT
        )
        self._settings.bind(
            "cache-dir", self.cache_dir_row, "text", Gio.SettingsBindFlags.DEFAULT
        )

        # directory browse buttons
        self.wine_prefix_browse.connect("clicked", self._on_browse, self.wine_prefix_row)
        self.log_dir_browse.connect("clicked", self._on_browse, self.log_dir_row)
        self.cache_dir_browse.connect("clicked", self._on_browse, self.cache_dir_row)

        # wine tool buttons
        self.winecfg_btn.connect("clicked", self._on_winecfg)
        self.regedit_btn.connect("clicked", self._on_regedit)
        self.wineboot_btn.connect("clicked", self._on_wineboot)
        self.open_prefix_btn.connect("clicked", self._on_open_prefix)

        # disable wine tools if wine is not installed
        if not WineBackend.is_installed():
            for btn in (self.winecfg_btn, self.regedit_btn, self.wineboot_btn, self.open_prefix_btn):
                btn.set_sensitive(False)
                btn.set_tooltip_text("Wine sistemde bulunamadı")

    def _prefix(self) -> str:
        """Resolve the current wine prefix from GSettings, expanding ~."""
        return Path(self._settings.get_string("wine-prefix")).expanduser()

    # wine tool launchers -------------------------------------------------

    def _on_winecfg(self, _btn: Gtk.Button) -> None:
        """Open Wine Configuration (winecfg) inside the configured prefix."""
        WineBackend.winecfg(wine_prefix=self._prefix())

    def _on_regedit(self, _btn: Gtk.Button) -> None:
        """Open the Windows Registry Editor."""
        WineBackend.run_command("regedit", wine_prefix=self._prefix())

    def _on_wineboot(self, _btn: Gtk.Button) -> None:
        """Restart the Wine server (wineboot -r)."""
        WineBackend.run_command("wineboot", "-r", wine_prefix=self._prefix())

    def _on_open_prefix(self, _btn: Gtk.Button) -> None:
        """Reveal the prefix directory in the system file manager."""
        path = self._prefix()
        path.mkdir(parents=True, exist_ok=True)
        Gio.AppInfo.launch_default_for_uri(
            Gio.File.new_for_path(str(path)).get_uri()
        )

    # directory picker helpers --------------------------------------------

    def _on_browse(self, button: Gtk.Button, row: Adw.EntryRow) -> None:
        """Open a folder chooser and set the row text to the selected path."""
        folder_dialog = Gtk.FileDialog.new()
        initial = Path(row.get_text()).expanduser()
        if initial.exists():
            folder_dialog.set_initial_folder(Gio.File.new_for_path(str(initial)))
        folder_dialog.select_folder(
            self, None, lambda d, r: self._on_folder_selected(d, r, row)
        )

    def _on_folder_selected(
        self, dialog: Gtk.FileDialog, result: Gio.AsyncResult, row: Adw.EntryRow
    ) -> None:
        """Handle the folder chooser response."""
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        if folder is not None:
            row.set_text(folder.get_path())
