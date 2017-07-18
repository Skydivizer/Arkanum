"""This module defines the format and parsing of .ART files."""
import io
from collections import namedtuple
from typing import Optional, List

from formats.helpers import FileStruct
from formats.art.flags import ArtFlags
from formats.art.frames import ArtFrame
from formats.art.palettes import ArtPalette
# Sources:
# Crypton's: Art File Format - Complete specification
# http://arcanum.game-alive.com/forums/viewtopic.php?f=6&t=53
# AxelStrem's ArtConverter
# https://github.com/AxelStrem/ArtConverter

# Convenience tuples for handling of headers.
_art_header = namedtuple('ArtHeader', [
    'flags', 'frame_rate', 'rotations', 'palette_pointers', 'key_frame',
    'num_frames', 'info_pointers', 'stage_sizes', 'stage_pointers'
])


def _get_frames_length(header):
    return header.num_frames * (
        1 if ArtFlags.fixed in header.flags else header.rotations)


def _get_num_frames(art):
    return len(art.frames) // (
        1 if ArtFlags.fixed in art.flags else art.rotations)


class Art(object):
    """An Art object is the deserialization of an .ART file.

    Attributes:
        flags: Desribes the type of the art object.
        frame_rate: Speed of the animation in frames per second.
        key_frame: Event attached to animation is triggered on this frame.
        palettes: List of palletes.
        frames: List of frames.
    """

    Flags = ArtFlags
    Frame = ArtFrame
    Palette = ArtPalette

    flags_format = "I"
    frame_rate_format = "I"
    rotations_format = "I"
    palette_pointer_format = "I"
    key_frame_format = "I"
    num_frames_format = "I"
    stage_info_pointer_format = "I"
    stage_size_format = "I"
    stage_pointer_format = "I"

    full_format = "<{}{}{}4{}{}{}8{}8{}8{}".format(
        flags_format, frame_rate_format, rotations_format,
        palette_pointer_format, key_frame_format, num_frames_format,
        stage_info_pointer_format, stage_size_format, stage_pointer_format)

    parser = FileStruct(full_format)

    def __init__(self,
                 flags,
                 frame_rate: int=8,
                 rotations: int=8,
                 key_frame: int=0,
                 palettes: Optional[List[Palette]]=None,
                 frames: Optional[List[Frame]]=None,
                 palette_pointers: Optional[List[int]]=None,
                 info_pointers: Optional[List[int]]=None,
                 stage_sizes: Optional[List[int]]=None,
                 stage_pointers: Optional[List[int]]=None,
                 **kwargs):
        """Initialize the Art object.

        Arguments:
            flags: Desribes the type of the art object.
            frame_rate: Speed of the animation in frames per second.
            rotations: Number of cardinal directions of the art.
            key_frame: Event attached to animation is triggered on this frame.
            palettes: List of palletes.
            frames: List of frames.
        """
        self.flags = flags
        self.frame_rate = frame_rate
        self.rotations = rotations
        self.key_frame = key_frame
        self.palettes = palettes if palettes else []
        self.frames = frames if frames else []

        # Legacy attributes
        self._palette_pointers = palette_pointers
        self._info_pointers = info_pointers
        self._stage_sizes = stage_sizes
        self._stage_pointers = stage_pointers

    @classmethod
    def read(cls, art_file_path: str) -> "Art":
        """Deserialize an art object from the given file.

        Arguments:
            art_file_path: Path to art file.

        Returns:
            A new Art object.
        """
        with open(art_file_path, "rb") as art_file:
            raw_header = cls.parser.unpack_from_file(art_file)
            header = _art_header(
                ArtFlags(raw_header[0]), *raw_header[1:3], raw_header[3:7],
                *raw_header[7:9], raw_header[9:17], raw_header[17:25],
                raw_header[25:33])
            palettes = [
                cls.Palette.read_from(art_file)
                for p in header.palette_pointers if p != 0
            ]
            frames = [
                cls.Frame.read_from(art_file, data=False)
                for _ in range(_get_frames_length(header))
            ]
            for frame in frames:
                frame.read_from(art_file, header=False)
            return cls(palettes=palettes, frames=frames, **header._asdict())

    def write(self, art_file_path: str) -> None:
        """Serialize the art object to a file at the given path.

        Arguments:
            art_file_path: Path to file.
        """
        with open(art_file_path, "wb") as art_file:

            def dflt_lst(item, size=(8,), fill=(0,)):
                return item if item else [
                    fill[s] for s in range(len(size)) for i in range(size[s])
                ]

            # Make sure there are as many (pseudo) pallete pointers as
            # there are palettes.
            n_pointers = len([p for p in self._palette_pointers if p != 0])
            if n_pointers != len(self.palettes):
                palette_pointers = *dflt_lst(self._palette_pointers,
                                             (len(self.palettes),
                                              4 - len(self.palettes)), (1, 0)),
            else:
                palette_pointers = self._palette_pointers

            self.parser.pack_into_file(art_file, self.flags, self.frame_rate,
                                       self.rotations, *palette_pointers,
                                       self.key_frame,
                                       _get_num_frames(self),
                                       *dflt_lst(self._info_pointers),
                                       *dflt_lst(self._stage_sizes),
                                       *dflt_lst(self._stage_pointers))
            for pallete in self.palettes:
                pallete.write_to(art_file)

            for frame in self.frames:
                frame.write_to(art_file, data=False)

            for frame in self.frames:
                frame.write_to(art_file, header=False)
