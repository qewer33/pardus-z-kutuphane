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

from .window import ZLibAppWindow


class PardusZKutuphaneApplication(Adw.Application):
    """The main application singleton class"""

    def __init__(self):
        super().__init__(
            application_id="tr.org.pardus.zkutuphane",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            resource_base_path="/tr/org/pardus/zkutuphane",
        )
        self.create_action("quit", lambda *_: self.quit(), ["<control>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ZLibAppWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        about = Adw.AboutDialog(
            application_name="Pardus Z-Kütüphane",
            application_icon="tr.org.pardus.zkutuphane",
            developer_name="Anadolu Penguenleri",
            version="0.1.0",
            developers=["Yunus Erdem ERGÜL", "Murat YALÇIN"],
            copyright="© 2026 Anadolu Penguenleri",
        )
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        print("app.preferences action activated")

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
