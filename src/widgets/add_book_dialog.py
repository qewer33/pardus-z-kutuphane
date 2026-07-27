from gi.repository import Adw, Gtk

from ..backend.publisherdetector import PublisherDetector, PublisherIconCache
from ..backend.tags import ALL_TAGS
from ..backend.typedetector import ExecutableType
from .card import UNKNOWN_PUBLISHER, ZLibCardData, set_image_from_file
from .type_pill import book_resource, type_icon

# launch categories
_FILE_CATEGORIES = [
    ("PDF Dosyası", ExecutableType.PDF),
    ("Linux Uygulaması", ExecutableType.ELF),
    ("Windows Uygulaması", ExecutableType.PE64),
]
_WEB_CATEGORY = ("Web Kitabı", ExecutableType.WEBBOOK)

# detected type
_CATEGORY_INDEX = {
    ExecutableType.PDF: 0,
    ExecutableType.ELF: 1,
    ExecutableType.APPIMAGE_V1: 1,
    ExecutableType.APPIMAGE_V2: 1,
    ExecutableType.PE32: 2,
    ExecutableType.PE64: 2,
}


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/add_book_dialog.ui")
class ZLibAddBookDialog(Adw.Window):
    """Dialog to review a book's metadata before adding it to the library"""

    __gtype_name__ = "ZLibAddBookDialog"

    book_icon_base = Gtk.Template.Child()
    book_icon_overlay = Gtk.Template.Child()
    title_row = Gtk.Template.Child()
    publisher_row = Gtk.Template.Child()
    publisher_dropdown_btn = Gtk.Template.Child()
    publisher_popover = Gtk.Template.Child()
    publisher_search_entry = Gtk.Template.Child()
    publisher_search_list = Gtk.Template.Child()
    publisher_value_label = Gtk.Template.Child()
    type_row = Gtk.Template.Child()
    type_dropdown_btn = Gtk.Template.Child()
    type_popover = Gtk.Template.Child()
    type_search_list = Gtk.Template.Child()
    type_value_label = Gtk.Template.Child()
    cancel_button = Gtk.Template.Child()
    add_button = Gtk.Template.Child()
    tag_flowbox = Gtk.Template.Child()
    tag_add_button = Gtk.Template.Child()
    tag_add_popover = Gtk.Template.Child()
    tag_search_entry = Gtk.Template.Child()
    tag_search_flowbox = Gtk.Template.Child()

    def __init__(
        self,
        card_data: ZLibCardData,
        on_confirm,
        title="Kitap Ekle",
        confirm_label="Ekle",
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.card_data = card_data
        self.on_confirm = on_confirm
        self.is_web = card_data.type == ExecutableType.WEBBOOK

        self.set_title(title)
        self.set_modal(True)
        self.set_default_size(420, 520)
        self.add_button.set_label(confirm_label)

        # tags
        self._tags: list[str] = list(card_data.tags or [])
        self._rebuild_tag_pills()

        pub_icon_path = PublisherIconCache.path_for(card_data.publisher)
        if pub_icon_path:
            set_image_from_file(self.book_icon_overlay, pub_icon_path)
            self._has_publisher_icon = True
        else:
            self._has_publisher_icon = False
            if card_data.publisher is not None:
                PublisherIconCache.fetch_async(
                    card_data.publisher, self._on_publisher_icon_ready
                )
        self.book_icon_overlay.set_visible(True)

        self.title_row.set_text(card_data.title)

        # publisher — ActionRow with searchable popover
        self._publishers = [UNKNOWN_PUBLISHER] + PublisherDetector.names()
        self._selected_publisher = card_data.publisher or UNKNOWN_PUBLISHER
        self.publisher_value_label.set_label(self._selected_publisher)
        self.publisher_row.set_activatable_widget(self.publisher_dropdown_btn)

        self.publisher_popover.connect("map", lambda _p: self._populate_publisher_search())
        self.publisher_search_entry.connect("search-changed", self._on_publisher_search)
        self.publisher_search_list.connect("row-activated", self._on_publisher_selected)

        # type — ActionRow with popover
        self._categories = [_WEB_CATEGORY] if self.is_web else _FILE_CATEGORIES
        self._selected_type_idx = 0 if self.is_web else _CATEGORY_INDEX.get(card_data.type, 0)
        self.type_value_label.set_label(self._categories[self._selected_type_idx][0])
        self.type_row.set_activatable_widget(self.type_dropdown_btn)
        self.type_dropdown_btn.set_sensitive(not self.is_web)

        self.type_popover.connect("map", lambda _p: self._populate_type_search())
        self.type_search_list.connect("row-activated", self._on_type_selected)
        self._update_book_image()

        self.cancel_button.connect("clicked", lambda _button: self.close())
        self.add_button.connect("clicked", self._on_add)

        self.tag_add_popover.connect("map", lambda _p: self._populate_tag_search())
        self.tag_search_entry.connect("search-changed", self._on_popup_search)
        self.tag_search_flowbox.connect("child-activated", self._on_popup_row_activated)
        self.tag_search_entry.connect("activate", self._on_popup_add)

    def present(self, parent=None):
        if parent is not None:
            self.set_transient_for(parent)
        super().present()

    def _rebuild_tag_pills(self) -> None:
        child = self.tag_flowbox.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.tag_flowbox.remove(child)
            child = nxt

        for tag in self._tags:
            pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

            label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            label_box.set_css_classes(["tag-pill-label"])
            label = Gtk.Label(label=tag)
            label_box.append(label)
            pill.append(label_box)

            remove_btn = Gtk.Button()
            remove_btn.set_css_classes(["tag-pill-remove"])
            icon = Gtk.Image.new_from_icon_name("window-close-symbolic")
            icon.set_pixel_size(10)
            remove_btn.set_child(icon)
            remove_btn.connect("clicked", lambda _btn, t=tag: self._remove_tag(t))
            pill.append(remove_btn)

            self.tag_flowbox.append(pill)

    def _remove_tag(self, tag: str) -> None:
        if tag in self._tags:
            self._tags.remove(tag)
            self._rebuild_tag_pills()

    def _populate_tag_search(self, filter_text: str = "") -> None:
        fb = self.tag_search_flowbox
        child = fb.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            fb.remove(child)
            child = nxt
        for tag in ALL_TAGS:
            if tag in self._tags:
                continue
            if filter_text and filter_text.lower() not in tag.lower():
                continue
            lbl = Gtk.Label(label=tag)
            lbl.set_halign(Gtk.Align.START)
            lbl.set_valign(Gtk.Align.START)
            lbl.set_css_classes(["tag-pill-large"])
            fb.append(lbl)

    def _on_popup_search(self, entry: Gtk.SearchEntry) -> None:
        self._populate_tag_search(entry.get_text())

    def _on_popup_add(self, _btn=None) -> None:
        selected = self.tag_search_flowbox.get_selected_children()
        if selected:
            tag = selected[0].get_child().get_label()
            if tag not in self._tags:
                self._tags.append(tag)
                self._rebuild_tag_pills()
        self.tag_add_popover.popdown()

    def _on_popup_row_activated(self, _fb, child) -> None:
        tag = child.get_child().get_label()
        if tag not in self._tags:
            self._tags.append(tag)
            self._rebuild_tag_pills()
        self.tag_add_popover.popdown()

    def _populate_publisher_search(self, filter_text: str = "") -> None:
        lb = self.publisher_search_list
        child = lb.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            lb.remove(child)
            child = nxt
        for publisher in self._publishers:
            if filter_text and filter_text.lower() not in publisher.lower():
                continue
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=publisher, halign=Gtk.Align.START)
            label.set_margin_start(6)
            label.set_margin_end(6)
            label.set_margin_top(4)
            label.set_margin_bottom(4)
            row.set_child(label)
            lb.append(row)

    def _on_publisher_search(self, entry: Gtk.SearchEntry) -> None:
        self._populate_publisher_search(entry.get_text())

    def _on_publisher_selected(self, _lb, row) -> None:
        publisher = row.get_child().get_label()
        self._selected_publisher = publisher
        self.publisher_value_label.set_label(publisher)
        self.publisher_popover.popdown()

    def _populate_type_search(self) -> None:
        lb = self.type_search_list
        child = lb.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            lb.remove(child)
            child = nxt
        for label, _ in self._categories:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=label, halign=Gtk.Align.START)
            lbl.set_margin_start(6)
            lbl.set_margin_end(6)
            lbl.set_margin_top(4)
            lbl.set_margin_bottom(4)
            row.set_child(lbl)
            lb.append(row)

    def _on_type_selected(self, _lb, row) -> None:
        label = row.get_child().get_label()
        for i, (lbl, _) in enumerate(self._categories):
            if lbl == label:
                self._selected_type_idx = i
                break
        self.type_value_label.set_label(label)
        self.type_popover.popdown()
        self._update_book_image()

    def _update_book_image(self) -> None:
        book_type = self._categories[self._selected_type_idx][1]
        self.book_icon_base.set_from_resource(book_resource(book_type))
        if not self._has_publisher_icon:
            self.book_icon_overlay.set_from_resource(type_icon(book_type))

    def _on_publisher_icon_ready(self, path: str) -> None:
        if self.card_data.publisher:
            set_image_from_file(self.book_icon_overlay, path)
            self.book_icon_overlay.set_visible(True)
            self._has_publisher_icon = True

    def _on_add(self, _button):
        card_data = self.card_data
        card_data.title = self.title_row.get_text().strip() or card_data.title

        card_data.publisher = None if self._selected_publisher == UNKNOWN_PUBLISHER else self._selected_publisher

        card_data.type = self._categories[self._selected_type_idx][1]
        card_data.tags = self._tags

        self.close()
        self.on_confirm(card_data)
