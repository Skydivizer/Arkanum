"""Gay."""
from formats.helpers import FileStruct

import io
import typing as t


class ArtPalette(object):
    """A color palette from an Art object.

    Each palette stores exactly 256 colors. The first index in the palette
    is reserved for a full transparent pixel, thus the actual color value
    in the pallete will be ignored.

    Attributes:
        data: A list of 256 color values.
    """

    pixel_format = "I"
    full_format = "<256{}".format(pixel_format)

    parser = FileStruct(full_format)

    def __init__(self, data: t.List[int]):
        """Initalize the pallete with color data.

        Arguments:
            data: A list of 256 color values.
        """
        self.data = data

    @classmethod
    def read_from(cls, art_file: io.FileIO) -> "Pallete":
        """Read the palette from a file.

        Will try to read 1024 bytes from the given file.

        Arguments:
            art_file: An open art file.

        Returns:
            A new Art Palette object.
        """
        data = cls.parser.unpack_from_file(art_file)
        return cls(data)

    def write_to(self, art_file: io.FileIO) -> None:
        """Write the pallete to a file.

        Will try to write 1024 bytes to the given file.

        Arguments:
            art_file: An open art file.
        """
        self.parser.pack_into_file(art_file, *self.data)
