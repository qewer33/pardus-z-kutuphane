from pathlib import Path

from gi.repository import Adw, Gio, GLib, GObject, Gtk

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

        self.wine_prefix_browse.connect("clicked", self._on_browse, self.wine_prefix_row)
        self.log_dir_browse.connect("clicked", self._on_browse, self.log_dir_row)
        self.cache_dir_browse.connect("clicked", self._on_browse, self.cache_dir_row)

    def _on_browse(self, button: Gtk.Button, row: Adw.EntryRow) -> None:
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
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        if folder is not None:
            row.set_text(folder.get_path())
