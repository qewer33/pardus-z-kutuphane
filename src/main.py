# main.py
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

import sys
from gettext import gettext as _

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, Gtk

from .widgets import PreferencesDialog
from .window import ZLibAppWindow


class PardusZKutuphaneApplication(Adw.Application):
    """The main application singleton class"""

    def __init__(self):
        super().__init__(
            application_id="tr.org.pardus.zkutuphane",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            resource_base_path="/tr/org/pardus/zkutuphane",
        )
        self._setup_style()
        self.create_action("quit", lambda *_: self.quit(), ["<control>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)

    def _setup_style(self):
        # TEMP: use libadwaita's empty base theme so only its own stylesheet
        # (loaded explicitly in the window) styles widgets. This bypasses the
        # system GTK theme and prevents the base theme from double-styling.
        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings is not None:
            gtk_settings.set_property("gtk-theme-name", "Adwaita-empty")
            gtk_settings.set_property("gtk-icon-theme-name", "Adwaita")

        # follow the system light/dark preference explicitly; libadwaita's
        # automatic detection relies on the xdg-desktop-portal settings, which
        # is often unavailable on X11 sessions (e.g. Pardus/GNOME X11), causing
        # the app to ignore the system color-scheme and stay light; reading
        # org.gnome.desktop.interface directly keeps the app in sync everywhere
        style_manager = Adw.StyleManager.get_default()

        # the user's explicit theme choice ("system"/"light"/"dark") lives in
        # the app's own GSettings; "system" falls back to following the desktop
        try:
            app_settings = Gio.Settings.new("tr.org.pardus.zkutuphane")
        except Exception:
            app_settings = None

        try:
            settings = Gio.Settings.new("org.gnome.desktop.interface")
        except Exception:
            settings = None

        # accessing a missing key is a fatal GLib error, so probe the schema
        # first; the legacy boolean key was dropped from newer schemas
        keys = []
        if settings is not None:
            try:
                keys = settings.list_keys()
            except Exception:
                keys = []

        has_legacy = "gtk-application-prefer-dark-theme" in keys
        has_scheme = "color-scheme" in keys

        def apply_system():
            prefer_dark = False
            if has_legacy:
                prefer_dark = settings.get_boolean("gtk-application-prefer-dark-theme")
            if prefer_dark:
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
                return
            scheme = settings.get_string("color-scheme") if has_scheme else "default"
            if scheme == "prefer-dark":
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            elif scheme == "prefer-light":
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            else:
                style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

        def apply():
            theme = "system"
            if app_settings is not None:
                theme = app_settings.get_string("theme")
            if theme == "light":
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            elif theme == "dark":
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            elif settings is not None:
                apply_system()
            else:
                style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

        apply()
        if app_settings is not None:
            app_settings.connect("changed::theme", lambda *_: apply())
        if settings is not None and has_scheme:
            settings.connect("changed::color-scheme", lambda *_: apply())
        if settings is not None and has_legacy:
            settings.connect(
                "changed::gtk-application-prefer-dark-theme", lambda *_: apply()
            )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ZLibAppWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        about_cls = Adw.AboutDialog if hasattr(Adw, "AboutDialog") else Adw.AboutWindow
        about = about_cls(
            application_name="Pardus Z-Kütüphane",
            application_icon="tr.org.pardus.zkutuphane",
            developer_name="Anadolu Penguenleri",
            version="0.1.0",
            developers=["Yunus Erdem ERGÜL", "Murat YALÇIN"],
            copyright="© 2026 Anadolu Penguenleri",
        )
        parent = self.props.active_window
        if isinstance(about, Adw.Dialog) if hasattr(Adw, "Dialog") else False:
            about.present(parent)
        else:
            about.set_transient_for(parent)
            about.set_modal(True)
            about.present()

    def on_preferences_action(self, widget, _):
        dialog = PreferencesDialog()
        dialog.present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    app = PardusZKutuphaneApplication()
    return app.run(sys.argv)
