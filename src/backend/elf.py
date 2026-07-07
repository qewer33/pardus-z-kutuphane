import os
import subprocess
from pathlib import Path

from ..util.logger import get_logger

logger = get_logger(os.path.basename(__file__))


class ELFError(Exception):
    """Raised for Wine-related errors"""


class ELFBackend:
    """Stateless ELF backend"""

    @staticmethod
    def launch(
        executable: str | Path,
        *,
        arguments: list[str] | None = None,
        workdir: str | Path | None = None,
    ) -> subprocess.Popen:
        """Launch an ELF executable"""

        executable = Path(executable).expanduser()

        if not executable.exists():
            raise FileNotFoundError(executable)

        command = [str(executable)]

        if arguments:
            command.extend(arguments)

        cwd = Path(workdir).expanduser() if workdir else executable.parent

        logger.info("Current working directory is: %s", cwd)
        logger.info("Launching ELF: %s %s", executable, arguments)

        return subprocess.Popen(
            command,
            cwd=cwd,
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
