import re
from pathlib import Path

_TURKISH_TABLE = str.maketrans({
    'ı': 'i', 'İ': 'i', 'I': 'i',
    'ş': 's', 'Ş': 's',
    'ç': 'c', 'Ç': 'c',
    'ö': 'o', 'Ö': 'o',
    'ü': 'u', 'Ü': 'u',
    'ğ': 'g', 'Ğ': 'g',
})

def _normalize(text: str) -> str:
    return text.translate(_TURKISH_TABLE).lower()

_UC = 'A-ZÇŞİĞÜÖ'
_LC = 'a-zçşığüö'

# Split at lowercase →  uppercase (e.g. "Hiz"|"Yayinlari")
_LOWER_UPPER = re.compile(fr'(?<=[{_LC}])(?=[{_UC}])')
# Split at uppercase →  uppercase+lowercase (e.g. "FDD"|"Yayinlari")
_UPPER_UPPER_LOWER = re.compile(fr'(?<=[{_UC}])(?=[{_UC}][{_LC}])')


def _split_into_words(text: str) -> list[str]:
    text = _LOWER_UPPER.sub('\x00', text)
    text = _UPPER_UPPER_LOWER.sub('\x00', text)
    return [p for p in text.split('\x00') if p]


class PublisherDetector:
    _TOKENS: frozenset[str] = frozenset({
        "hiz", "isler", "ankara", "palme", "esen", "zafer",
        "limit", "sinav", "kida", "tudem", "fdd", "lider",
        "murat", "okyanus", "paraf", "puan", "zirve",
        "bilgi", "mileniyum", "cap", "apotemi",
    })

    @classmethod
    def detect(cls, path: str | Path) -> str | None:
        stem = Path(path).stem
        tokens = re.split(r"[ _-]+", stem)
        for token in tokens:
            if not token:
                continue
            parts = _split_into_words(token)
            for part in parts:
                normalized = _normalize(part)
                if normalized in cls._TOKENS:
                    return normalized
        return None
