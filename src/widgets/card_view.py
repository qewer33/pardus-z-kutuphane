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

from gi.repository import Gio, GObject, Gtk

from ..util.normalizer import Normalizer
from .card import ZLibCard, ZLibCardData


class ZLibCardItem(GObject.Object):
    """Thin GObject wrapper so ZLibCardData can live in a Gio.ListStore"""

    __gtype_name__ = "ZLibCardItem"

    def __init__(self, data: ZLibCardData):
        super().__init__()
        self.data = data


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/card_view.ui")
class ZLibCardView(Gtk.FlowBox):
    """Card view grid for library entries"""

    __gtype_name__ = "ZLibCardView"

    __gsignals__ = {
        "card-selected": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        # emitted whenever cards are added, removed or reordered
        "library-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

        # the store is the main model
        # filter model applies the search, sort model orders by launch count
        self.store = Gio.ListStore.new(ZLibCardItem)
        self._search_text = ""
        self._filter = Gtk.CustomFilter.new(self._match)
        self._filter_model = Gtk.FilterListModel.new(self.store, self._filter)
        self._sorter = Gtk.CustomSorter.new(self._sort_by_launch_count)
        self._sort_model = Gtk.SortListModel.new(self._filter_model, self._sorter)
        self.bind_model(self._sort_model, self._create_card)
        self.store.connect("items-changed", lambda *_: self.emit("library-changed"))

        self.connect("selected-children-changed", self._on_selection_changed)

    @property
    def cards_data_list(self) -> list[ZLibCardData]:
        return [self.store.get_item(i).data for i in range(self.store.get_n_items())]

    def set_search_text(self, text: str) -> None:
        # use Normalizer to handle turkish letters
        self._search_text = Normalizer.normalize(text.strip())
        self._filter.changed(Gtk.FilterChange.DIFFERENT)

    def _match(self, item: ZLibCardItem, *_) -> bool:
        if not self._search_text:
            return True
        data = item.data
        haystack = Normalizer.normalize(f"{data.title} {data.publisher or ''}")
        return self._search_text in haystack

    def _sort_by_launch_count(self, a: ZLibCardItem, b: ZLibCardItem, _user_data=None) -> int:
        return b.data.launch_count - a.data.launch_count

    def invalidate_sort(self) -> None:
        self._sorter.changed(Gtk.SorterChange.DIFFERENT)

    def _create_card(self, item: ZLibCardItem) -> ZLibCard:
        return ZLibCard(item.data)

    def add_card(self, card_data: ZLibCardData):
        self.store.append(ZLibCardItem(card_data))

    def get_selected_card(self):
        children = self.get_selected_children()
        if not children:
            return None
        return children[0].get_child().data

    def refresh_selected_card(self):
        children = self.get_selected_children()
        if children:
            children[0].get_child().refresh()

    def remove_selected_card(self):
        children = self.get_selected_children()
        if not children:
            return
        # map the selected widget back to its store index by identity, since a
        # child's index is relative to the filtered view, not the store
        card_data = children[0].get_child().data
        for i in range(self.store.get_n_items()):
            if self.store.get_item(i).data is card_data:
                self.store.remove(i)
                return

    def _on_selection_changed(self, _flowbox):
        self.emit("card-selected", self.get_selected_card())
