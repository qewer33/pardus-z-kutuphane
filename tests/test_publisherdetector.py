import importlib.util
import sys
from pathlib import Path

import pytest

# load the publisherdetector module without triggering backend/__init__.py
# (which pulls in GTK-dependent modules that can't be imported headlessly)
_MOD_PATH = (
    Path(__file__).resolve().parent.parent / "src" / "backend" / "publisherdetector.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "backend.publisherdetector", _MOD_PATH, submodule_search_locations=[]
)
_MOD = importlib.util.module_from_spec(_SPEC)
sys.modules["backend.publisherdetector"] = _MOD
_SPEC.loader.exec_module(_MOD)

Normalizer = _MOD.Normalizer
PublisherDetector = _MOD.PublisherDetector


class TestNormalizer:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("ı", "i"),
            ("I", "i"),
            ("İ", "i"),
            ("ş", "s"),
            ("Ş", "s"),
            ("ç", "c"),
            ("Ç", "c"),
            ("ö", "o"),
            ("Ö", "o"),
            ("ü", "u"),
            ("Ü", "u"),
            ("ğ", "g"),
            ("Ğ", "g"),
            ("Yayınları", "yayinlari"),
            ("Yayincilik", "yayincilik"),
            ("Yayınevi", "yayinevi"),
            ("hız", "hiz"),
            ("işler", "isler"),
            ("çap", "cap"),
            ("hello", "hello"),
            ("HIZ", "hiz"),
            ("FDD", "fdd"),
            ("123", "123"),
            ("", ""),
        ],
    )
    def test_normalize(self, raw, expected):
        assert Normalizer.normalize(raw) == expected

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Hız Yayınları", ["hiz", "yayinlari"]),
            ("Bilgi Sarmal Yayınları", ["bilgi", "sarmal", "yayinlari"]),
            ("Hız_Yayınları", ["hiz", "yayinlari"]),
            ("PALME_YAYINCILIK", ["palme", "yayincilik"]),
            ("Hız-Yayınları", ["hiz", "yayinlari"]),
            ("HizYayinlari", ["hiz", "yayinlari"]),
            ("BilgiYayinevi", ["bilgi", "yayinevi"]),
            ("345Yayinlari", ["345", "yayinlari"]),
            ("FDDYayinlari", ["fdd", "yayinlari"]),
            ("FDDYayinlariFizik", ["fdd", "yayinlari", "fizik"]),
            ("HizYayinlari-Matematik", ["hiz", "yayinlari", "matematik"]),
            ("Hız Yayınları_8Sınıf", ["hiz", "yayinlari", "8", "sinif"]),
            ("hiz", ["hiz"]),
            ("bilgisayar", ["bilgisayar"]),
            ("HIZ", ["hiz"]),
            ("OKYANUS", ["okyanus"]),
            ("345", ["345"]),
            ("ABCYayin", ["abc", "yayin"]),
            ("8Sinif", ["8", "sinif"]),
            ("Sinav8Sinif", ["sinav", "8", "sinif"]),
            ("Çap Yayınları", ["cap", "yayinlari"]),
            ("İşler Yayınları", ["isler", "yayinlari"]),
            ("", []),
        ],
    )
    def test_words(self, raw, expected):
        assert Normalizer.words(raw) == expected


class TestPublisherDetector:
    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("Hiz.exe", "Hız Yayınları"),
            ("hiz.exe", "Hız Yayınları"),
            ("HIZ.exe", "Hız Yayınları"),
            ("Hız.exe", "Hız Yayınları"),
            ("işler.exe", "İşler Yayınları"),
            ("isler.exe", "İşler Yayınları"),
            ("ankara.exe", "Ankara Yayıncılık"),
            ("palme.exe", "Palme Yayınevi"),
            ("esen.exe", "Esen Yayınları"),
            ("zafer.exe", "Zafer Yayınları"),
            ("limit.exe", "Limit Yayınları"),
            ("sinav.exe", "Sınav Yayınları"),
            ("kida.exe", "Kida Yayınları"),
            ("tudem.exe", "Tudem Yayınları"),
            ("fdd.exe", "FDD Yayınları"),
            ("FDD.exe", "FDD Yayınları"),
            ("lider.exe", "Lider Yayınları"),
            ("murat.exe", "Murat Yayınları"),
            ("okyanus.exe", "Okyanus Yayınları"),
            ("paraf.exe", "Paraf Yayınları"),
            ("puan.exe", "Puan Yayınları"),
            ("zirve.exe", "Zirve Yayınları"),
            ("cap.exe", "Çap Yayınları"),
            ("Çap.exe", "Çap Yayınları"),
            ("apotemi.exe", "Apotemi Yayınları"),
            ("mileniyum.exe", "Mileniyum Yayınları"),
            ("HizYayinlari.exe", "Hız Yayınları"),
            ("HizYayinlari-Matematik.exe", "Hız Yayınları"),
            ("Hiz Yayinlari - Matematik.exe", "Hız Yayınları"),
            ("Hız Yayınları_Matematik_9.exe", "Hız Yayınları"),
            ("İşlerYayınları_Türkçe.exe", "İşler Yayınları"),
            ("Palme_Yayincilik_Fizik.exe", "Palme Yayınevi"),
            ("EsenYayinlariKimya.exe", "Esen Yayınları"),
            ("ZaferYayinlariKitap.exe", "Zafer Yayınları"),
            ("LimitYayinlariGeometri.exe", "Limit Yayınları"),
            ("SınavYayınları_TYT.exe", "Sınav Yayınları"),
            ("KidaYayinlari.exe", "Kida Yayınları"),
            ("TudemYayinlari.exe", "Tudem Yayınları"),
            ("FDDYayinlariFizik.exe", "FDD Yayınları"),
            ("LiderYayinlari.exe", "Lider Yayınları"),
            ("MuratYayinlari.exe", "Murat Yayınları"),
            ("OkyanusYayinlari.exe", "Okyanus Yayınları"),
            ("ParafYayinlari.exe", "Paraf Yayınları"),
            ("PuanYayinlari.exe", "Puan Yayınları"),
            ("ZirveYayinlari.exe", "Zirve Yayınları"),
            ("ÇapYayınları.exe", "Çap Yayınları"),
            ("ApotemiYayinlari.exe", "Apotemi Yayınları"),
            ("MileniyumYayinlari.exe", "Mileniyum Yayınları"),
            ("Bilgi Sarmal Yayınları.exe", "Bilgi Sarmal Yayınları"),
            ("bilgi sarmal.exe", "Bilgi Sarmal Yayınları"),
            ("BilgiSarmalYayinlari.exe", "Bilgi Sarmal Yayınları"),
            ("BilgiSarmal.exe", "Bilgi Sarmal Yayınları"),
            ("345 Yayınları.exe", "345 Yayınları"),
            ("345_Yayinlari.exe", "345 Yayınları"),
            ("345Yayinlari.exe", "345 Yayınları"),
            ("345 yayin.exe", "345 Yayınları"),
            ("OKYANUS.exe", "Okyanus Yayınları"),
            ("FDD.exe", "FDD Yayınları"),
            ("bilgisayar.exe", None),
            ("palmiye.exe", None),
            ("limitless.exe", None),
            ("sinavlari.exe", None),
            ("muratli.exe", None),
            ("random_uygulama.exe", None),
            ("", None),
        ],
    )
    def test_detect(self, filename, expected):
        assert PublisherDetector.detect(filename) == expected

    def test_detect_with_full_path(self):
        result = PublisherDetector.detect("/home/user/Downloads/HizYayinlari.exe")
        assert result == "Hız Yayınları"

    def test_detect_with_relative_path(self):
        result = PublisherDetector.detect("./HizYayinlari.exe")
        assert result == "Hız Yayınları"

    def test_detect_with_dotted_filename(self):
        result = PublisherDetector.detect("Hiz.Yayinlari.exe")
        assert result == "Hız Yayınları"

    def test_detect_publisher_names_are_distinct(self):
        names = list(PublisherDetector._PUBLISHERS.values())
        assert len(names) == len(set(names))
