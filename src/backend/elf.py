import os
import shutil
import subprocess
from pathlib import Path


class ELFError(Exception):
    """Raised for Wine-related errors."""


class ELFBackend:
    def __init__(
        self,
        workdir: str | Path | None = None,
    ):
        self.workdir = Path(workdir).expanduser() if workdir else None

    def launch(
        self,
        executable: str | Path,
        arguments: list[str] | None = None,
    ) -> subprocess.Popen:
        """Launch an ELF executable."""

        executable = Path(executable).expanduser()

        if not executable.exists():
            raise FileNotFoundError(executable)

        command = [
            str(executable)
        ]

        if arguments:
            command.extend(arguments)

        cwd = self.workdir or executable.parent

        return subprocess.Popen(
            command,
            cwd=cwd,
            env=os.environ.copy(),
        )
