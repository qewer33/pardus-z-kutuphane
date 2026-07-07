import os
import shutil
import subprocess
from pathlib import Path

from gi.repository import GLib

from ..util.logger import get_logger

logger = get_logger(os.path.basename(__file__))


class WineError(Exception):
    """Raised for Wine-related errors"""


class WineBackend:
    """Stateless Wine backend"""

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
    def ensure_prefix(
        wine_prefix: str | Path,
        *,
        wine_binary: str = "wine",
    ) -> None:
        """Initialize the wineprefix if it's not already set up"""

        if not WineBackend.is_installed(wine_binary):
            raise WineError("Wine is not installed.")

        prefix = Path(wine_prefix).expanduser()
        sentinel = prefix / "drive_c" / "windows" / "system32" / "shell32.dll"

        if sentinel.exists():
            return

        # broken prefix, remoe it
        if prefix.exists():
            logger.warning("Removing broken/incomplete wineprefix: %s", prefix)
            shutil.rmtree(prefix)

        logger.info("Initializing wineprefix: WINEPREFIX=%s wineboot -i", prefix)

        prefix.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            ["wineboot", "-i"],
            env=WineBackend._environment(prefix),
        )

        if result.returncode != 0 or not sentinel.exists():
            raise WineError(
                f"Failed to initialize wineprefix at {prefix} "
                f"(wineboot exit code {result.returncode})."
            )

    @staticmethod
    def launch(
        executable: str | Path,
        *,
        arguments: list[str] | None = None,
        wine_prefix: str | Path | None = None,
        wine_binary: str = "wine",
        workdir: str | Path | None = None,
    ) -> subprocess.Popen:
        """Launch a Windows executable"""

        if not WineBackend.is_installed(wine_binary):
            raise WineError("Wine is not installed.")

        if wine_prefix is not None:
            WineBackend.ensure_prefix(wine_prefix, wine_binary=wine_binary)

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
