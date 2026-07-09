import webbrowser
from types import SimpleNamespace


class WebbookBackend:
    """Stateless WebBook backend"""
    @staticmethod
    def launch(url: str):
        webbrowser.open(url)
        return SimpleNamespace(stdout=(), wait=lambda: None)
