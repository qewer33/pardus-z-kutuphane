from pathlib import Path

ALL_TAGS = sorted({
    "Matematik",
    "Geometri",
    "Problemler",
    "Paragraf",
    "Dil Bilgisi",
    "Türkçe",
    "Türk Dili ve Edebiyatı",
    "Edebiyat",
    "Dil ve Anlatım",
    "Fizik",
    "Kimya",
    "Biyoloji",
    "Tarih",
    "İnkılap Tarihi",
    "Coğrafya",
    "Felsefe",
    "Psikoloji",
    "Sosyoloji",
    "Mantık",
    "Din Kültürü ve Ahlak Bilgisi",
    "İngilizce",
    "Almanca",
    "Fransızca",
    "Sosyal Bilgiler",
    "Fen Bilimleri",
    "Hayat Bilgisi",
    "Yabancı Dil",
    "Rehberlik",
    "Sağlık Bilgisi",
    "Trafik ve İlk Yardım",
    "Demokrasi ve İnsan Hakları",
    "Vatandaşlık",
    "TYT",
    "AYT",
    "YKS",
    "KPSS",
    "ALES",
    "DGS",
    "LGS",
    "Soru Bankası",
    "Konu Anlatımı",
})

_TAG_KEYWORDS: dict[frozenset[str], str] = {
    frozenset({"matematik", "math", "mat", "problem", "problemler", "geometri", "geo", "trigonometri", "fonksiyon", "sayilar", "sayılar", "integral", "turev", "türev", "limit", "polinom", "olasilik", "olasılık", "istatistik"}): "Matematik",
    frozenset({"geometri", "geo", "acilar", "açılar", "ucgen", "üçgen", "cember", "çember", "daire", "kati", "katı", "analitik"}): "Geometri",
    frozenset({"problem", "problemler"}): "Problemler",
    frozenset({"paragraf"}): "Paragraf",
    frozenset({"dil bilgisi", "dilbilgisi"}): "Dil Bilgisi",
    frozenset({"turkce", "türkçe", "turkish"}): "Türkçe",
    frozenset({"edebiyat", "literature", "turk dili", "türk dili", "dil ve anlatim", "dil ve anlatım"}): "Türk Dili ve Edebiyatı",
    frozenset({"fizik", "physics"}): "Fizik",
    frozenset({"kimya", "chemistry"}): "Kimya",
    frozenset({"biyoloji", "biology", "biyoloji"}): "Biyoloji",
    frozenset({"tarih", "history", "tarih"}): "Tarih",
    frozenset({"inkılap", "inkilap", "inkılap tarihi"}): "İnkılap Tarihi",
    frozenset({"cografya", "coğrafya", "geography"}): "Coğrafya",
    frozenset({"felsefe", "philosophy"}): "Felsefe",
    frozenset({"psikoloji", "psychology"}): "Psikoloji",
    frozenset({"sosyoloji", "sociology"}): "Sosyoloji",
    frozenset({"mantik", "mantık", "logic"}): "Mantık",
    frozenset({"din kulturu", "din kültürü", "din", "ahlak"}): "Din Kültürü ve Ahlak Bilgisi",
    frozenset({"ingilizce", "ingilizce", "english"}): "İngilizce",
    frozenset({"almanca", "german"}): "Almanca",
    frozenset({"fransizca", "fransızca", "french"}): "Fransızca",
    frozenset({"sosyal", "sosyal bilgiler"}): "Sosyal Bilgiler",
    frozenset({"fen", "fen bilimleri"}): "Fen Bilimleri",
    frozenset({"hayat bilgisi"}): "Hayat Bilgisi",
    frozenset({"yabanci dil", "yabancı dil"}): "Yabancı Dil",
    frozenset({"rehberlik"}): "Rehberlik",
    frozenset({"saglik", "sağlık", "saglik bilgisi", "sağlık bilgisi"}): "Sağlık Bilgisi",
    frozenset({"trafik", "ilk yardim", "ilk yardım"}): "Trafik ve İlk Yardım",
    frozenset({"demokrasi", "insan haklari", "insan hakları"}): "Demokrasi ve İnsan Hakları",
    frozenset({"vatandaslik", "vatandaşlık"}): "Vatandaşlık",
    frozenset({"tyt", "temel yeterlilik"}): "TYT",
    frozenset({"ayt", "alan yeterlilik"}): "AYT",
    frozenset({"yks", "yuksekogretim", "yükseköğretim"}): "YKS",
    frozenset({"kpss"}): "KPSS",
    frozenset({"ales"}): "ALES",
    frozenset({"dgs"}): "DGS",
    frozenset({"lgs"}): "LGS",
    frozenset({"soru bankasi", "soru bankası", "sb", "test", "deneme", "soru"}): "Soru Bankası",
    frozenset({"konu anlatimi", "konu anlatımı", "anlatim", "anlatım", "konu"}): "Konu Anlatımı",
}


def _tokenize(text: str) -> list[str]:
    from .publisherdetector import Normalizer
    return [Normalizer.normalize(w) for w in Normalizer.WORD.findall(text)]


class TagDetector:
    """Stateless Tag Detector Class."""

    @classmethod
    def detect_from_filename(cls, path: str | Path) -> list[str]:
        """Auto-detection of tags from given string (or path)"""
        stem = Path(path).stem
        tokens = set(_tokenize(stem))
        matched: set[str] = set()
        for keywords, tag in _TAG_KEYWORDS.items():
            if tokens & keywords:
                matched.add(tag)
        return sorted(matched)

    @classmethod
    def detect_from_publisher(cls, publisher: str | None) -> list[str]:
        """Not used right now. Will be used if we want tags for publishers"""
        if publisher is None:
            return []
        tokens = set(_tokenize(publisher))
        matched: set[str] = set()
        for keywords, tag in _TAG_KEYWORDS.items():
            if tokens & keywords:
                matched.add(tag)
        return sorted(matched)
