"""This module defines the format and parsing of .ART files."""
import io
from formats.helpers import FileStruct
from collections import namedtuple
from typing import Optional, List
from operator import attrgetter

# Sources:
# Crypton's: Art File Format - Complete specification (site is down)
# http://arcanum.game-alive.com/forums/viewtopic.php?f=6&t=53&sid=e59e8c820ae06438c0cfccf47192386f
# AxelStrem's ArtConverter
# https://github.com/AxelStrem/ArtConverter

# Convenience tuples for handling of headers.
_art_header = namedtuple('ArtHeader', [
    'flags', 'frame_rate', 'rotations', 'palette_pointers', 'key_frame',
    'num_frames', 'info_pointers', 'stage_sizes', 'stage_pointers'
])

_art_frame_header = namedtuple('ArtFrameHeader', [
    'width', 'height', 'size', 'offset_x', 'offset_y', 'delta_x', 'delta_y'
])
_art_frame_header.getter = attrgetter(*_art_frame_header._fields)


class Art(object):
    """An Art object is the deserialization of an .ART file.

    Attributes:
        flags: Desribes the type of the art object.
        frame_rate: Speed of the animation in frames per second.
        rotations: Number of cardinal directions of the art.
        key_frame: Animation is triggered on the frame with this index.
        palettes: List of palletes.
        frames: List of frames.
    """

    flags_format = "I"
    frame_rate_format = "I"
    num_rotations_format = "I"
    palette_pointer_format = "I"
    key_frame_format = "I"
    num_frames_format = "I"
    info_pointer_format = "I"
    stage_size_format = "I"
    stage_pointer_format = "I"

    full_format = "<{}{}{}4{}{}{}8{}8{}8{}".format(
        flags_format, frame_rate_format, num_rotations_format,
        palette_pointer_format, key_frame_format, num_frames_format,
        info_pointer_format, stage_size_format, stage_pointer_format)

    parser = FileStruct(full_format)

    class Frame(object):
        """A single frame of the Art object.

        Frames do not define the actual color values, but they store the index
        of a color in a palette.

        Attributes:
            width: Width in pixels.
            height: Height in pixels
            offset_x: Offset of rendering in x position.
            offset_y: Offset of rendering in y position.
            delta_x: Change of x position when object is moving.
            delta_y: Change of y position when object is moving
            data: Compressed palette indices.
            size: Size of the compressed indices in bytes.
        """

        dimension_format = "I"
        size_format = "I"
        offset_format = "i"
        delta_format = "i"

        full_format = "<2{}{}2{}2{}".format(dimension_format, size_format,
                                            offset_format, delta_format)
        parser = FileStruct(full_format)

        index_format = "b"

        def __init__(self,
                     width: int=0,
                     height: int=0,
                     size: int=0,
                     offset_x: int=0,
                     offset_y: int=0,
                     delta_x: int=0,
                     delta_y: int=0,
                     data: Optional[List[int]]=None):
            """Initialize the art frame.

            Attributes:
                width: Width in pixels.
                height: Height in pixels
                offset_x: Offset of rendering in x position.
                offset_y: Offset of rendering in y position.
                delta_x: Change of x position when object is moving.
                delta_y: Change of y position when object is moving
                data: Compressed palette indices.
                size: Size of the compressed indices in bytes.
            """
            self.width = width
            self.height = height
            self.size = size
            self.offset_x = offset_x
            self.offset_y = offset_y
            self.delta_x = delta_x
            self.delta_y = delta_y
            self.data = data

            self.read_from = self.__read_from

        @classmethod
        def read_data_from(cls, art_file: io.FileIO, size) -> List[int]:
            """Read pallete index data from file.

            Tries to read "size" bytes.

            Arguments:
                art_file: An open art file.
                size: Size of frame data in bytes.

            Returns:
                A list of "size" indices.
            """
            parser = FileStruct('<{}{}'.format(size, cls.index_format))
            return parser.unpack_from_file(art_file)

        @classmethod
        def read_header_from(cls, art_file: io.FileIO) -> dict:
            """Read the frame header from a file.

            Arguments:
                art_file: An open art file.

            Returns:
                A mapping from attribute names to their values.
            """
            return _art_frame_header(*cls.parser.unpack_from_file(art_file))

        @classmethod
        def read_from(cls, art_file: io.FileIO, header: bool=True,
                      data: bool=True) -> "Frame":
            """Read the frame header and/or data from a file.

            Functionality differs if called as class or instance method. If
            called as class method a new Art Frame object created. Otherwise
            the read data will be attached to the current object.

            Arguments:
                art_file: An open art file.
                header: Set to false if the header should not be read.
                data: Set to false if the frame data should not be read.

            Returns:
                If called as classmethod a new Art Frame object, else nothing.
            """
            header_data = cls.read_header_from(art_file) if header else None
            frame_data = cls.read_data_from(art_file,
                                            header_data.size) if data else None

            return cls(data=frame_data, **header_data._asdict())

        def __read_from(self, art_file: io.FileIO, header=True,
                        data=True) -> None:
            header_data = self.read_header_from(art_file) if header else None
            if header_data:
                for key, val in header_data.items():
                    setattr(self, key, val)
            if data:
                self.data = self.read_data_from(art_file, self.size)

        def write_to(self,
                     art_file: io.FileIO,
                     header: bool=True,
                     data: bool=True) -> None:
            """Serialize the frame or some part of it into a file stream.

            Arguments:
                art_file: An open art file.
                header: Set to false if the header should not be written.
                data: Set to false if the frame data should not be written.
            """
            if header:
                header_data = _art_frame_header.getter(self)
                self.parser.pack_into_file(art_file, header_data)
            if data:
                parser = FileStruct(
                    '<{}{}'.format(self.size, self.index_format))
                parser.pack_into_file(art_file, self.data)

    class Palette(object):
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

        def __init__(self, data: List[int]):
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
            key_frame: Animation is triggered on the frame with this index.
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
        if art_file_path.endswith("BadArt.ART"):
            return None
        with open(art_file_path, "rb") as art_file:

            raw_header = cls.parser.unpack_from_file(art_file)
            header = _art_header(*raw_header[0:3], raw_header[3:7],
                                 *raw_header[7:9], raw_header[9:17],
                                 raw_header[17:25], raw_header[25:33])


            palettes = [
                cls.Palette.read_from(art_file)
                for _ in header.palette_pointers
            ]
            frames = [
                cls.Frame.read_from(art_file, data=False)
                for _ in range(header.num_frames * header.rotations)
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
                        fill[s] for s in range(len(size))
                        for i in range(size[s])
                    ]

                # Make sure there are as many (pseudo) pallete pointers as
                # there are palettes.
                n_pointers = len([p for p in self.palette_pointers if p != 0])
                if n_pointers != len(self.palettes):
                    palette_pointers = *dflt_lst(
                        self.palette_pointers,
                        (len(self.palettes), 4 - len(self.palettes)), (1, 0)),
                else:
                    palette_pointers = self.palette_pointers

                cls.parser.pack_into_file(art_file, self.flags, self.rotations,
                                          palette_pointers, self.key_frame,
                                          len(self.frames),
                                          *dflt_lst(self.info_pointers),
                                          *dflt_lst(self.stage_pointers))
                for pallete in self.palettes:
                    pallete.write_to(art_file)

                for frame in self.frames:
                    frame.write_to(art_file, data=False)

                for frame in self.frames:
                    frame.write_to(art_file, header=False)
