# window.py
#
# Copyright 2026 qewer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .elf import ELFBackend
from .typedetector import ExecutableType
from .wine import WineBackend


class Launcher:
    """Stateless Launcher class"""

    @staticmethod
    def launch(app):
        """Main launch method for launching Cards"""

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
