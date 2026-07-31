import logging
from pathlib import Path

from gi.repository import GLib

APP_NAME = "tr.org.pardus.zkutuphane"
SCHEMA_ID = "tr.org.pardus.zkutuphane"

def _default_log_dir() -> Path:
    try:
        from gi.repository import Gio

        source = Gio.SettingsSchemaSource.get_default()
        if source is not None and source.lookup(SCHEMA_ID, True) is not None:
            settings = Gio.Settings(schema_id=SCHEMA_ID)
            val = settings.get_string("log-dir")
            if val:
                return Path(val).expanduser()
    except Exception:
        pass
    return Path(GLib.get_user_state_dir()) / APP_NAME


LOG_DIR = _default_log_dir()
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }

    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname:<8}{self.RESET}"
        return super().format(record)


file_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

console_formatter = ColorFormatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(file_formatter)

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(console_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        _file_handler,
        _console_handler,
    ],
)


def get_logger(name: str):
    return logging.getLogger(name)
