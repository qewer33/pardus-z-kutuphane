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
class ZLibAddBookDialog(Adw.Dialog):
    """Dialog to review a book's metadata before adding it to the library"""

    __gtype_name__ = "ZLibAddBookDialog"

    book_icon_base = Gtk.Template.Child()
    book_icon_overlay = Gtk.Template.Child()
    title_row = Gtk.Template.Child()
    publisher_row = Gtk.Template.Child()
    type_row = Gtk.Template.Child()
    cancel_button = Gtk.Template.Child()
    add_button = Gtk.Template.Child()
    tag_flowbox = Gtk.Template.Child()
    tag_add_button = Gtk.Template.Child()

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

        # publisher dropdown
        self._publishers = [UNKNOWN_PUBLISHER] + PublisherDetector.names()
        self.publisher_row.set_model(Gtk.StringList.new(self._publishers))
        if card_data.publisher in self._publishers:
            self.publisher_row.set_selected(self._publishers.index(card_data.publisher))

        # type dropdown, locked to Web for web books, else launch categories
        self._categories = [_WEB_CATEGORY] if self.is_web else _FILE_CATEGORIES
        labels = [label for label, _ in self._categories]
        self.type_row.set_model(Gtk.StringList.new(labels))
        if not self.is_web:
            self.type_row.set_selected(_CATEGORY_INDEX.get(card_data.type, 0))
        self.type_row.set_sensitive(not self.is_web)

        # tint the book cover to match the selected type, live
        self.type_row.connect("notify::selected", self._on_type_changed)
        self._update_book_image()

        self.cancel_button.connect("clicked", lambda _button: self.close())
        self.add_button.connect("clicked", self._on_add)
        self.tag_add_button.connect("clicked", self._open_tag_popup)

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

    def _open_tag_popup(self, _button) -> None:
        popover = Gtk.Popover()
        popover.set_parent(self.tag_add_button)
        popover.set_position(Gtk.PositionType.BOTTOM)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
            margin_top=6,
            margin_bottom=6,
            margin_start=6,
            margin_end=6,
        )
        box.set_size_request(250, -1)

        popup_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        popup_header.append(Gtk.Label(label="", hexpand=True))
        box.append(popup_header)

        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Etiket Ara...")
        box.append(search_entry)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_valign(Gtk.Align.START)
        scrolled.set_min_content_height(200)
        scrolled.set_max_content_height(300)

        search_flowbox = Gtk.FlowBox()
        search_flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        search_flowbox.set_max_children_per_line(1)
        search_flowbox.set_column_spacing(4)
        search_flowbox.set_row_spacing(4)
        search_flowbox.set_homogeneous(False)
        scrolled.set_child(search_flowbox)
        box.append(scrolled)

        popover.set_child(box)

        def populate(filter_text: str = "") -> None:
            child = search_flowbox.get_first_child()
            while child:
                nxt = child.get_next_sibling()
                search_flowbox.remove(child)
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
                search_flowbox.append(lbl)

        def on_search_changed(entry):
            populate(entry.get_text())

        def on_add_clicked(_btn):
            selected = search_flowbox.get_selected_children()
            if selected:
                tag = selected[0].get_child().get_label()
                if tag not in self._tags:
                    self._tags.append(tag)
                    self._rebuild_tag_pills()
            popover.popdown()

        def on_row_activated(_fb, child):
            tag = child.get_child().get_label()
            if tag not in self._tags:
                self._tags.append(tag)
                self._rebuild_tag_pills()
            popover.popdown()

        search_entry.connect("search-changed", on_search_changed)
        search_entry.connect("activate", on_add_clicked)

        # lazy-populate on first map so the popup auto-sizes with content
        populated = False

        def on_map(_p):
            nonlocal populated
            if not populated:
                populate()
                populated = True

        popover.connect("map", on_map)

        add_btn.connect("clicked", on_add_clicked)
        search_flowbox.connect("child-activated", on_row_activated)

        popover.popup()

    def _on_type_changed(self, _row, _param) -> None:
        self._update_book_image()

    def _update_book_image(self) -> None:
        book_type = self._categories[self.type_row.get_selected()][1]
        self.book_icon_base.set_from_resource(book_resource(book_type))
        if not self._has_publisher_icon:
            self.book_icon_overlay.set_from_icon_name(type_icon(book_type))

    def _on_publisher_icon_ready(self, path: str) -> None:
        if self.card_data.publisher:
            set_image_from_file(self.book_icon_overlay, path)
            self.book_icon_overlay.set_visible(True)
            self._has_publisher_icon = True

    def _on_add(self, _button):
        card_data = self.card_data
        card_data.title = self.title_row.get_text().strip() or card_data.title

        publisher = self._publishers[self.publisher_row.get_selected()]
        card_data.publisher = None if publisher == UNKNOWN_PUBLISHER else publisher

        card_data.type = self._categories[self.type_row.get_selected()][1]
        card_data.tags = self._tags

        self.close()
        self.on_confirm(card_data)
