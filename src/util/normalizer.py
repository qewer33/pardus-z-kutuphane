import re


class Normalizer:
    """Utility class for normalizing Turkish strings into ASCII"""

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
