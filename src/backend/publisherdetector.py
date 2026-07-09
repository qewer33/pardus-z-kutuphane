import re
from pathlib import Path


class Normalizer:
    # uppercase and lowercase Turkish chars
    UC, LC = "A-ZÇŞİĞÜÖ", "a-zçşığüö"

    # fold Turkish letters to ASCII so keys can be written plainly
    TURKISH = str.maketrans("ıİIşŞçÇöÖüÜğĞ", "iiissccoouugg")

    # a "word" is an acronym, a capitalized/lowercase word, or a number
    # splits both separators and camelCase
    WORD = re.compile(rf"[{UC}]+(?![{LC}])|[{UC}]?[{LC}]+|[0-9]+")

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize a Turkish word to plain ASCII"""
        return text.translate(Normalizer.TURKISH).lower()

    @staticmethod
    def words(text: str) -> list[str]:
        """Split text into an ordered list of normalized words"""
        return [Normalizer.normalize(word) for word in Normalizer.WORD.findall(text)]


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
        "345": "345 Yayınları",
        "aydin", "Aydın Yayınları"
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
