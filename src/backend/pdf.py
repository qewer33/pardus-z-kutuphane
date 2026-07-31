import subprocess
import shutil

from ..util.logger import get_logger
import os

logger = get_logger(os.path.basename(__file__))


class PDFError(Exception):
    """Raised for PDF-related errors"""


class PDFBackend:
    @staticmethod
    def launch(path: str) -> subprocess.Popen:
        if not shutil.which("xdg-open"):
            raise PDFError("xdg-open bulunamadı")
        logger.info("Opening PDF: %s", path)
        return subprocess.Popen(
            ["xdg-open", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
