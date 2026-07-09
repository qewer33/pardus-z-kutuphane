from gi.repository import Adw, Gtk

from ..backend.publisherdetector import PublisherDetector, PublisherIconCache
from ..backend.typedetector import ExecutableType
from .card import UNKNOWN_PUBLISHER, ZLibCardData

# launch categories
_FILE_CATEGORIES = [
    ("Linux Uygulaması", ExecutableType.ELF),
    ("Windows Uygulaması", ExecutableType.PE64),
]
_WEB_CATEGORY = ("Web Kitabı", ExecutableType.WEBBOOK)

# detected type
_CATEGORY_INDEX = {
    ExecutableType.ELF: 0,
    ExecutableType.APPIMAGE_V1: 0,
    ExecutableType.APPIMAGE_V2: 0,
    ExecutableType.PE32: 1,
    ExecutableType.PE64: 1,
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

        pub_icon_path = PublisherIconCache.path_for(card_data.publisher)
        if pub_icon_path:
            self.book_icon_overlay.set_from_file(pub_icon_path)
            self.book_icon_overlay.set_visible(True)
        elif card_data.publisher is None:
            self.book_icon_overlay.set_from_icon_name("dialog-question-symbolic")
            self.book_icon_overlay.set_visible(True)
        else:
            self.book_icon_overlay.set_visible(False)
            PublisherIconCache.fetch_async(card_data.publisher, self._on_publisher_icon_ready)

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

        self.cancel_button.connect("clicked", lambda _button: self.close())
        self.add_button.connect("clicked", self._on_add)

    def _on_publisher_icon_ready(self, path: str) -> None:
        if self.card_data.publisher:
            self.book_icon_overlay.set_from_file(path)
            self.book_icon_overlay.set_visible(True)

    def _on_add(self, _button):
        card_data = self.card_data
        card_data.title = self.title_row.get_text().strip() or card_data.title

        publisher = self._publishers[self.publisher_row.get_selected()]
        card_data.publisher = None if publisher == UNKNOWN_PUBLISHER else publisher

        card_data.type = self._categories[self.type_row.get_selected()][1]

        self.close()
        self.on_confirm(card_data)
