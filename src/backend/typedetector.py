from enum import Enum

import filetype


class ExecutableType(Enum):
    UNKNOWN = "unknown"

    ELF = "elf"

    APPIMAGE_V1 = "appimage-v1"
    APPIMAGE_V2 = "appimage-v2"

    PE32 = "pe32"
    PE64 = "pe64"

    PDF = "pdf"

    WEBBOOK = "webbook"


class TypeDetector:
    @staticmethod
    def get_executable_type(path):
        kind = filetype.guess(path)

        if kind is None:
            return ExecutableType.UNKNOWN

        #
        # PDF documents
        #
        if kind.extension == "pdf":
            return ExecutableType.PDF

        #
        # Windows PE executables
        #
        if kind.extension == "exe":
            with open(path, "rb") as f:
                f.seek(0x3C)
                pe_offset = int.from_bytes(f.read(4), "little")

                f.seek(pe_offset + 4)
                machine = int.from_bytes(f.read(2), "little")

            if machine == 0x8664:
                return ExecutableType.PE64

            return ExecutableType.PE32

        #
        # ELF executables
        #
        if kind.extension == "elf":
            with open(path, "rb") as f:
                data = f.read()

            # AppImage Type 2 contains the AI\x02 magic.
            if b"AI\x02" in data:
                return ExecutableType.APPIMAGE_V2

            # AppImage Type 1 contains the "AppImage" string.
            if b"AppImage" in data:
                return ExecutableType.APPIMAGE_V1

            return ExecutableType.ELF

        return ExecutableType.UNKNOWN
