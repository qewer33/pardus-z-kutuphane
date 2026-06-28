# card_view.py
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


from .card import ZLibCardData, ZLibCard


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/card_view.ui")
class ZLibCardView(Gtk.FlowBox):
    __gtype_name__ = "ZLibCardView"

    card_icon = Gtk.Template.Child("card_icon")
    card_title = Gtk.Template.Child("card_title")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

        self.cards_data_list: [ZLibCardData] = []  # main data list

    def add_card(self, card_data: ZLibCardData):
        self.cards_data_list.append(card_data)
        card = ZLibCard(card_data)
        self.insert(card, -1)

