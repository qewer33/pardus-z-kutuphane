from dataclasses import dataclass, field
from pathlib import Path

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from ..backend.publisherdetector import PublisherIconCache
from ..backend.tags import TagDetector
from ..backend.typedetector import ExecutableType
from .type_pill import ZLibTypePill, book_resource, pill_info, type_icon

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
    tags: list[str] | None = None
    arguments: list[str] | None = None
    wine_prefix: Path = field(
        default_factory=lambda: (
            Path(GLib.get_user_data_dir()) / "tr.org.pardus.zkutuphane" / "wineprefix"
        )
    )
    running: bool = False
    launch_count: int = 0
    log_buffer: Gtk.TextBuffer = field(default_factory=Gtk.TextBuffer)

    def to_dict(self) -> dict:
        """Serialize the persistent fields"""
        return {
            "title": self.title,
            "icon": self.icon,
            "path": self.path,
            "type": self.type.value,
            "publisher": self.publisher,
            "tags": self.tags,
            "arguments": self.arguments,
            "wine_prefix": str(self.wine_prefix),
            "launch_count": self.launch_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ZLibCardData":
        return cls(
            title=data["title"],
            icon=data["icon"],
            path=data["path"],
            type=ExecutableType(data["type"]),
            publisher=data.get("publisher"),
            tags=data.get("tags"),
            arguments=data["arguments"],
            wine_prefix=Path(data["wine_prefix"]),
            launch_count=data.get("launch_count", 0),
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
        self._type_class = None
        self.refresh()

        gesture = Gtk.GestureClick()
        gesture.set_button(0)
        gesture.connect("pressed", self._on_double_click)
        self.add_controller(gesture)

    def _on_double_click(self, _gesture, n_press, _x, _y):
        if n_press == 2:
            self.activate_action("win.launch-card", None)

    def refresh(self) -> None:
        """Sync the widgets with the current card data."""
        self.card_title.set_text(self.data.title)
        self.card_publisher.set_text(self.data.publisher or UNKNOWN_PUBLISHER)
        self.type_pill.set_book_type(self.data.type)
        self.card_icon_base.set_from_resource(book_resource(self.data.type))

        _, _, css_class = pill_info(self.data.type)
        if self._type_class:
            self.remove_css_class(self._type_class)
        self.add_css_class(css_class)
        self._type_class = css_class

        pub_icon_path = PublisherIconCache.path_for(self.data.publisher)
        if pub_icon_path:
            set_image_from_file(self.card_icon_overlay, pub_icon_path)
        else:
            # no cached publisher logo: fall back to the book's type icon, and
            # fetch the logo (if the publisher has one) to swap in when ready
            self.card_icon_overlay.set_from_resource(type_icon(self.data.type))
            if self.data.publisher is not None:
                PublisherIconCache.fetch_async(
                    self.data.publisher, self._on_publisher_icon_ready
                )
        self.card_icon_overlay.set_visible(True)

    def _on_publisher_icon_ready(self, path: str) -> None:
        if self.data.publisher:
            set_image_from_file(self.card_icon_overlay, path)
            self.card_icon_overlay.set_visible(True)
