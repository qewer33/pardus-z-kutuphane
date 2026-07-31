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
    def _find_real_binary(binary: str) -> str:
        """If <binary> resolves to a shell wrapper, prefer /usr/bin/<binary>.

        Some distributions (e.g., Pardus ETAP 23) ship wine as a wrapper
        script earlier in PATH that overrides WINEPREFIX and other
        environment variables. Detect the wrapper and use the real
        system binary instead so our WINEPREFIX is respected.
        """
        path = shutil.which(binary)
        if path is None:
            return binary
        try:
            with open(path, "rb") as f:
                if not f.readline().startswith(b"#!"):
                    return path  # real binary, not a script
        except (IOError, OSError, UnicodeDecodeError):
            return binary
        # it's a wrapper script, use the real system binary
        hardcoded = f"/usr/bin/{binary}"
        if os.path.isfile(hardcoded) or os.path.islink(hardcoded):
            return hardcoded
        return binary

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

        # bypass wrapper scripts that override WINEPREFIX
        # this is added for Pardus ETAP
        wineboot = WineBackend._find_real_binary("wineboot")

        prefix = Path(wine_prefix).expanduser()
        sentinel = prefix / "drive_c" / "windows" / "system32" / "shell32.dll"

        if sentinel.exists():
            return

        # broken prefix, remove it
        if prefix.exists():
            logger.warning("Removing broken/incomplete wineprefix: %s", prefix)
            shutil.rmtree(prefix)

        prefix.mkdir(parents=True, exist_ok=True)

        # try wineboot -u (update) first, which is more lenient than -i
        # on older Wine / systems with missing dependencies; fall back
        # to -i if that's not available
        for flag in ("-u", "-i"):
            logger.info("Initializing wineprefix: WINEPREFIX=%s %s %s", prefix, wineboot, flag)
            result = subprocess.run(
                [wineboot, flag],
                env=WineBackend._environment(prefix),
                capture_output=True, text=True,
            )
            if result.returncode == 0 and sentinel.exists():
                return

        raise WineError(
            f"Failed to initialize wineprefix at {prefix}.\n"
            f"  wineboot stderr: {result.stderr.strip()}\n"
            f"  wineboot stdout: {result.stdout.strip()}\n"
            f"  exit code: {result.returncode}\n\n"
            "Try running 'wine winecfg' manually, or check that the "
            "wine32 package is installed (dpkg --add-architecture i386 "
            "&& apt install wine32)."
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

        # bypass wrapper scripts that override WINEPREFIX
        # this is added for Pardus ETAP
        wine_binary = WineBackend._find_real_binary(wine_binary)

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
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    @staticmethod
    def winecfg(
        *,
        wine_prefix: str | Path | None = None,
        wine_binary: str = "wine",
    ) -> subprocess.Popen:
        logger.info("Opening winecfg")

        wine_binary = WineBackend._find_real_binary(wine_binary)

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

        wine_binary = WineBackend._find_real_binary(wine_binary)

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

        wine_binary = WineBackend._find_real_binary(wine_binary)

        return subprocess.Popen(
            [wine_binary, *args],
            env=WineBackend._environment(wine_prefix),
        )
