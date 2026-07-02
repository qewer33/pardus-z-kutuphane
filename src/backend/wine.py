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
    def __init__(
        self,
        wine_binary: str = "wine",
        wine_prefix: str | Path | None = Path(GLib.get_user_data_dir()) / "tr.org.pardus.zkutuphane" / "wineprefix",
        workdir: str | Path | None = None,
    ):
        self.wine_binary = wine_binary
        self.wine_prefix = Path(wine_prefix).expanduser() if wine_prefix else None
        self.workdir = Path(workdir).expanduser() if workdir else None
        wine_prefix.mkdir(parents=True, exist_ok=True)

    def is_installed(self) -> bool:
        """Return True if the Wine executable exists."""
        return shutil.which(self.wine_binary) is not None

    def _environment(self) -> dict:
        env = os.environ.copy()

        if self.wine_prefix:
            env["WINEPREFIX"] = str(self.wine_prefix)

        return env

    def launch(
        self,
        executable: str | Path,
        arguments: list[str] | None = None,
    ) -> subprocess.Popen:
        """Launch a Windows executable."""

        if not self.is_installed():
            raise WineError("Wine is not installed.")

        executable = Path(executable).expanduser()

        if not executable.exists():
            raise FileNotFoundError(executable)

        command = [
            self.wine_binary,
            str(executable),
        ]

        if arguments:
            command.extend(arguments)

        cwd = self.workdir or executable.parent

        logger.info(f"Current working directory is: {cwd}")
        logger.info(f"Launching PE: WINEPREFIX={self.wine_prefix} {self.wine_binary} {executable} {arguments}")
        return subprocess.Popen(
            command,
            cwd=cwd,
            env=self._environment(),
        )

    def winecfg(self):
        """Open winecfg."""
        logger.info("Opening winecfg")
        subprocess.Popen(
            [self.wine_binary, "winecfg"],
            env=self._environment(),
        )

    def explorer(self, path: str | Path):
        """Open Wine Explorer."""
        logger.info("Opening explorer")
        subprocess.Popen(
            [self.wine_binary, "explorer", str(path)],
            env=self._environment(),
        )

    def run_command(self, *args):
        """Run any Wine command."""
        logger.info(f"Running command: {self.wine_binary} {args}")
        subprocess.Popen(
            [self.wine_binary, *args],
            env=self._environment(),
        )
