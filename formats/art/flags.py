"""Fk."""
import enum


class ArtFlags(enum.IntFlag):
    """This class indicates the type of art in the file.

    :param fixed: The art does look equal in each rotation. Thus the
        frames are only present once.
    :param mobile: The art is used during motion. This indicates that the delta
        values of the frames are used.
    :param font: The art is a font.
    :param facade: The art is a facade file.
    :param unknown: Only set on some eye candy art files.
    """

    fixed = 1 << 0
    mobile = 1 << 1
    font = 1 << 2
    facade = 1 << 3
    unknown = 1 << 4
