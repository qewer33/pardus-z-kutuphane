import json
import threading
from pathlib import Path

from gi.repository import GLib

from ..util.normalizer import Normalizer


class PublisherDetector:
    # normalized token to proper publisher display name
    _PUBLISHERS: dict[str, str] = {
        "hiz": "Hız Yayınları",
        "isler": "İşler Yayınları",
        "ankara": "Ankara Yayıncılık",
        "palme": "Palme Yayınevi",
        "esen": "Esen Yayınları",
        "zafer": "Zafer Yayınları",
        "limit": "Limit Yayınları",
        "sinav": "Sınav Yayınları",
        "kida": "Kida Yayınları",
        "tudem": "Tudem Yayınları",
        "fdd": "FDD Yayınları",
        "lider": "Lider Yayınları",
        "murat": "Murat Yayınları",
        "okyanus": "Okyanus Yayınları",
        "paraf": "Paraf Yayınları",
        "puan": "Puan Yayınları",
        "zirve": "Zirve Yayınları",
        "bilgi sarmal": "Bilgi Sarmal Yayınları",
        "mileniyum": "Mileniyum Yayınları",
        "cap": "Çap Yayınları",
        "apotemi": "Apotemi Yayınları",
        "ucdortbes": "ÜçDörtBeş Yayınları",
        "aydin": "Aydın Yayınları",
    }

    @classmethod
    def names(cls) -> list[str]:
        """Sorted list of known publisher display names."""
        return sorted(set(cls._PUBLISHERS.values()))

    @classmethod
    def detect(cls, path: str | Path) -> str | None:
        stem = Path(path).stem

        parts = Normalizer.words(stem)

        # match publisher keys (one or more tokens)
        # trying the longest keys first
        keys = sorted(cls._PUBLISHERS, key=lambda k: len(k.split()), reverse=True)
        for key in keys:
            key_tokens = key.split()
            span = len(key_tokens)
            for i in range(len(parts) - span + 1):
                if parts[i : i + span] == key_tokens:
                    return cls._PUBLISHERS[key]
        return None


def _load_publisher_logos() -> dict[str, str]:
    # installed:  {pkgdatadir}/publisher_icons.json
    # dev source: {project_root}/data/publisher_icons.json
    module_dir = Path(__file__).resolve().parent
    pkgdatadir = module_dir.parent.parent
    candidates = [
        pkgdatadir / "publisher_icons.json",
        pkgdatadir / "data" / "publisher_icons.json",
    ]
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text())
    return {}


_PUBLISHER_LOGOS = _load_publisher_logos()

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _cache_dir() -> Path:
    try:
        from gi.repository import Gio

        source = Gio.SettingsSchemaSource.get_default()
        if source is not None and source.lookup("tr.org.pardus.zkutuphane", True) is not None:
            settings = Gio.Settings(schema_id="tr.org.pardus.zkutuphane")
            val = settings.get_string("cache-dir")
            if val:
                return Path(val).expanduser() / "publisher_icons"
    except Exception:
        pass
    return (
        Path(GLib.get_user_cache_dir())
        / "tr.org.pardus.zkutuphane"
        / "publisher_icons"
    )


class PublisherIconCache:
    _CACHE_DIR: Path | None = None

    @classmethod
    def _get_dir(cls) -> Path:
        if cls._CACHE_DIR is None:
            cls._CACHE_DIR = _cache_dir()
        return cls._CACHE_DIR

    @classmethod
    def path_for(cls, publisher: str | None) -> str | None:
        if publisher is None:
            return None
        url = _PUBLISHER_LOGOS.get(publisher)
        if url is None:
            return None
        name = cls._url_to_name(url)
        path = cls._get_dir() / name
        if path.exists():
            return str(path)
        return None

    @classmethod
    def _url_to_name(cls, url: str) -> str:
        return Path(url.split("//")[-1].split("/")[0]).stem + ".png"

    @classmethod
    def fetch_async(cls, publisher: str, on_ready: callable) -> None:
        url = _PUBLISHER_LOGOS.get(publisher)
        if url is None:
            return

        def _fetch():
            import os

            from ..util.logger import get_logger

            _logger = get_logger(os.path.basename(__file__))

            cache_dir = cls._get_dir()
            cache_dir.mkdir(parents=True, exist_ok=True)
            name = cls._url_to_name(url)
            path = cache_dir / name
            if path.exists():
                GLib.idle_add(on_ready, str(path))
                return
            try:
                from urllib.parse import quote
                from urllib.request import Request, urlopen

                # percent-encode non-ASCII path chars, and send a browser
                # User-Agent so servers that 403 the default urllib agent serve
                # the image
                safe_url = quote(url, safe=":/?&=#%@+,;")
                request = Request(safe_url, headers={"User-Agent": _USER_AGENT})
                with urlopen(request, timeout=15) as response:
                    path.write_bytes(response.read())

                if path.exists() and path.stat().st_size > 512:
                    GLib.idle_add(on_ready, str(path))
                else:
                    path.unlink(missing_ok=True)
                    _logger.error(
                        "Publisher icon too small or missing: %s (%s)", publisher, url
                    )
            except Exception as e:
                path.unlink(missing_ok=True)
                _logger.error(
                    "Failed to fetch publisher icon for %s (%s): %s", publisher, url, e
                )

        threading.Thread(target=_fetch, daemon=True).start()
