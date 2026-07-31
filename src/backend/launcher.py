from .elf import ELFBackend
from .pdf import PDFBackend
from .typedetector import ExecutableType
from .webbook import WebbookBackend
from .wine import WineBackend
from ..util.logger import get_logger

import os
import stat

logger = get_logger(os.path.basename(__file__))

class Launcher:
    """Stateless Launcher class"""

    @staticmethod
    def ensure_execute_perm(app):
        """Add execute permissions (required if ELF, optional if wine)"""
        if app.type not in (ExecutableType.WEBBOOK, ExecutableType.PDF):
            try:
                if not os.access(app.path, os.X_OK):
                    logger.info("File %s does not have user execute permissions, running chmod", app.path) 
                    os.chmod(app.path, os.stat(app.path).st_mode | stat.S_IEXEC)
            except OSError:
                return
    
    @staticmethod
    def launch(app):
        """
        Main launch method for launching Cards
        Note that all of the backends are compatible with the ZLibCardData class
        """

        Launcher.ensure_execute_perm(app)
        
        if app.type in (
            ExecutableType.ELF,
            ExecutableType.APPIMAGE_V1,
            ExecutableType.APPIMAGE_V2,
        ):
            return ELFBackend.launch(executable=app.path)
        elif app.type in (
            ExecutableType.PE32,
            ExecutableType.PE64,
        ):
            return WineBackend.launch(
                executable=app.path,
                arguments=app.arguments,
                wine_prefix=app.wine_prefix,
            )
        elif app.type == ExecutableType.PDF:
            return PDFBackend.launch(path=app.path)
        elif app.type == ExecutableType.WEBBOOK:
            return WebbookBackend.launch(url=app.path)
