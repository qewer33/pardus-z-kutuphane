# pdf.py
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

import subprocess
import shutil

from ..util.logger import get_logger
import os

logger = get_logger(os.path.basename(__file__))


class PDFError(Exception):
    """Raised for PDF-related errors"""


class PDFBackend:
    @staticmethod
    def launch(path: str) -> subprocess.Popen:
        if not shutil.which("xdg-open"):
            raise PDFError("xdg-open bulunamadı")
        logger.info("Opening PDF: %s", path)
        return subprocess.Popen(
            ["xdg-open", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
