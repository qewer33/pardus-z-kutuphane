import os
import shutil
import subprocess
from pathlib import Path


class WineError(Exception):
    """Raised for Wine-related errors."""


class WineBackend:
    def __init__(
        self,
        wine_binary: str = "wine",
        prefix: str | Path | None = None,
        workdir: str | Path | None = None,
    ):
        self.wine_binary = wine_binary
        self.prefix = Path(prefix).expanduser() if prefix else None
        self.workdir = Path(workdir).expanduser() if workdir else None

    def is_installed(self) -> bool:
        """Return True if the Wine executable exists."""
        return shutil.which(self.wine_binary) is not None

    def _environment(self) -> dict:
        env = os.environ.copy()

        if self.prefix:
            env["WINEPREFIX"] = str(self.prefix)

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

        return subprocess.Popen(
            command,
            cwd=cwd,
            env=self._environment(),
        )

    def winecfg(self):
        """Open winecfg."""
        subprocess.Popen(
            [self.wine_binary, "winecfg"],
            env=self._environment(),
        )

    def explorer(self, path: str | Path):
        """Open Wine Explorer."""
        subprocess.Popen(
            [self.wine_binary, "explorer", str(path)],
            env=self._environment(),
        )

    def run_command(self, *args):
        """Run any Wine command."""
        subprocess.Popen(
            [self.wine_binary, *args],
            env=self._environment(),
        )
