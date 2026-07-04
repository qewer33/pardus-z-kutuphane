import os
import shutil
import subprocess
from pathlib import Path

from gi.repository import GLib

from ..util.logger import get_logger

logger = get_logger(os.path.basename(__file__))

class WineError(Exception):
    """Raised for Wine-related errors."""

class WineBackend:
    """Stateless Wine backend."""

    def __new__(cls):
        raise TypeError("WineBackend is a static utility class")
    
    @staticmethod
    def is_installed(wine_binary: str = "wine") -> bool:
        return shutil.which(wine_binary) is not None

    @staticmethod
    def _environment(wine_prefix: str | Path | None = None) -> dict:
        env = os.environ.copy()

        if wine_prefix is not None:
            env["WINEPREFIX"] = str(Path(wine_prefix).expanduser())

        return env

    @staticmethod
    def launch(
        executable: str | Path,
        *,
        arguments: list[str] | None = None,
        wine_prefix: str | Path | None = None,
        wine_binary: str = "wine",
        workdir: str | Path | None = None,
    ) -> subprocess.Popen:
        """Launch a Windows executable."""

        if not WineBackend.is_installed(wine_binary):
            raise WineError("Wine is not installed.")

        executable = Path(executable).expanduser()

        if not executable.exists():
            raise FileNotFoundError(executable)

        command = [wine_binary, str(executable)]

        if arguments:
            command.extend(arguments)

        cwd = Path(workdir).expanduser() if workdir else executable.parent

        logger.info(
            "Launching PE: WINEPREFIX=%s %s %s %s",
            wine_prefix,
            wine_binary,
            executable,
            arguments,
        )

        return subprocess.Popen(
            command,
            cwd=cwd,
            env=WineBackend._environment(wine_prefix),
        )

    @staticmethod
    def winecfg(
        *,
        wine_prefix: str | Path | None = None,
        wine_binary: str = "wine",
    ) -> subprocess.Popen:
        logger.info("Opening winecfg")

        return subprocess.Popen(
            [wine_binary, "winecfg"],
            env=WineBackend._environment(wine_prefix),
        )

    @staticmethod
    def explorer(
        path: str | Path,
        *,
        wine_prefix: str | Path | None = None,
        wine_binary: str = "wine",
    ) -> subprocess.Popen:
        logger.info("Opening explorer")

        return subprocess.Popen(
            [wine_binary, "explorer", str(path)],
            env=WineBackend._environment(wine_prefix),
        )

    @staticmethod
    def run_command(
        *args,
        wine_prefix: str | Path | None = None,
        wine_binary: str = "wine",
    ) -> subprocess.Popen:
        logger.info("Running command: %s %s", wine_binary, args)

        return subprocess.Popen(
            [wine_binary, *args],
            env=WineBackend._environment(wine_prefix),
        )
