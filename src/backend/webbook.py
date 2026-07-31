import webbrowser
from types import SimpleNamespace


class WebbookBackend:
    """Stateless WebBook backend"""
    @staticmethod
    def launch(url: str):
        """Launch a webbook with system's preferred web browser."""
        webbrowser.open(url)
        return SimpleNamespace(stdout=(), wait=lambda: None)
