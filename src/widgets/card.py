from dataclasses import dataclass, field
from pathlib import Path

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from ..backend.publisherdetector import PublisherIconCache
from ..backend.typedetector import ExecutableType
from .type_pill import ZLibTypePill, book_resource, type_icon

UNKNOWN_PUBLISHER = "Bilinmeyen Yayıncı"


def set_image_from_file(image: Gtk.Image, path: str) -> None:
    """Load a file into a Gtk.Image via GdkTexture"""
    try:
        image.set_from_paintable(Gdk.Texture.new_from_filename(path))
    except GLib.Error:
        image.set_visible(False)


@dataclass
class ZLibCardData:
    """Library card dataclass"""

    title: str
    icon: str
    path: str
    type: ExecutableType
    publisher: str | None = None
    arguments: list[str] | None = None
    wine_prefix: Path = field(
        default_factory=lambda: (
            Path(GLib.get_user_data_dir()) / "tr.org.pardus.zkutuphane" / "wineprefix"
        )
    )
    running: bool = False
    log_buffer: Gtk.TextBuffer = field(default_factory=Gtk.TextBuffer)

    def to_dict(self) -> dict:
        """Serialize the persistent fields"""
        return {
            "title": self.title,
            "icon": self.icon,
            "path": self.path,
            "type": self.type.value,
            "publisher": self.publisher,
            "arguments": self.arguments,
            "wine_prefix": str(self.wine_prefix),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ZLibCardData":
        return cls(
            title=data["title"],
            icon=data["icon"],
            path=data["path"],
            type=ExecutableType(data["type"]),
            publisher=data.get("publisher"),
            arguments=data["arguments"],
            wine_prefix=Path(data["wine_prefix"]),
        )


@Gtk.Template(resource_path="/tr/org/pardus/zkutuphane/card.ui")
class ZLibCard(Adw.Bin):
    """Library card widget element"""

    __gtype_name__ = "ZLibCard"

    card_icon_base = Gtk.Template.Child()
    card_icon_overlay = Gtk.Template.Child()
    card_pill_container = Gtk.Template.Child()
    card_title = Gtk.Template.Child()
    card_publisher = Gtk.Template.Child()

    def __init__(self, data: ZLibCardData, **kwargs):
        super().__init__(**kwargs)

        self.data = data
        self.type_pill = ZLibTypePill()
        self.card_pill_container.append(self.type_pill)
        self.refresh()

    def refresh(self) -> None:
        """Sync the widgets with the current card data."""
        self.card_title.set_text(self.data.title)
        self.card_publisher.set_text(self.data.publisher or UNKNOWN_PUBLISHER)
        self.type_pill.set_book_type(self.data.type)
        self.card_icon_base.set_from_resource(book_resource(self.data.type))

        pub_icon_path = PublisherIconCache.path_for(self.data.publisher)
        if pub_icon_path:
            set_image_from_file(self.card_icon_overlay, pub_icon_path)
        else:
            # no cached publisher logo: fall back to the book's type icon, and
            # fetch the logo (if the publisher has one) to swap in when ready
            self.card_icon_overlay.set_from_icon_name(type_icon(self.data.type))
            if self.data.publisher is not None:
                PublisherIconCache.fetch_async(
                    self.data.publisher, self._on_publisher_icon_ready
                )
        self.card_icon_overlay.set_visible(True)

    def _on_publisher_icon_ready(self, path: str) -> None:
        if self.data.publisher:
            set_image_from_file(self.card_icon_overlay, path)
            self.card_icon_overlay.set_visible(True)
