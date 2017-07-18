"""Test."""
from formats.helpers import FileStruct
import typing as t
import io
import collections
import operator

_art_frame_header = collections.namedtuple('ArtFrameHeader', [
    'width', 'height', 'size', 'offset_x', 'offset_y', 'delta_x', 'delta_y'
])
_art_frame_header.getter = operator.attrgetter(*_art_frame_header._fields)


class ArtFrame(object):
    """A single frame of the Art object.

    Frames do not define the actual color values, but they store the index
    of a color in a palette.

    Attributes:
        width: Width in pixels.
        height: Height in pixels
        offset_x: Offset of rendering in x position.
        offset_y: Offset of rendering in y position.g
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

    pixel_format = "b"

    def __init__(self,
                 width: int=0,
                 height: int=0,
                 size: int=0,
                 offset_x: int=0,
                 offset_y: int=0,
                 delta_x: int=0,
                 delta_y: int=0,
                 data: t.Optional[t.List[int]]=None):
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
        self._size = size
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.delta_x = delta_x
        self.delta_y = delta_y
        self.data = data

        self.read_from = self.__read_from

    @property
    def size(self) -> int:
        """Get the size of the frame data.

        Returns:
            The size of the frame data in bytes.
        """
        return len(self.data) if self.data else self._size

    @classmethod
    def read_data_from(cls, art_file: io.FileIO, size) -> t.List[int]:
        """Read pallete index data from file.

        Tries to read "size" bytes.

        Arguments:
            art_file: An open art file.
            size: Size of frame data in bytes.

        Returns:
            A list of "size" indices.
        """
        parser = FileStruct('<{}{}'.format(size, cls.pixel_format))
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
                  data: bool=True) -> t.Optional["Frame"]:
        """Read the frame header and/or data from a file.

        Functionality differs if called as class or instance method. If
        called as class method a new Art Frame object created. Otherwise
        the read data will be attached to the current object.

        Arguments:
            art_file: An open art file.
            header: Set to false if the header should not be read. This
                must be true when creating a new instance.
            data: Set to false if the frame data should not be read.

        Returns:
            If called as classmethod a new Art Frame object, else nothing.
        """
        header_data = cls.read_header_from(art_file)
        frame_data = cls.read_data_from(art_file,
                                        header_data.size) if data else None

        return cls(data=frame_data, **header_data._asdict())

    def __read_from(self,
                    art_file: io.FileIO,
                    header: bool=True,
                    data: bool=True) -> None:
        header_data = self.read_header_from(art_file) if header else None
        if header_data:
            for key, val in header_data.items():
                setattr(self, key, val)
        if data:
            self.data = self.read_data_from(art_file, self.size)

    def write_to(self, art_file: io.FileIO, header: bool=True,
                 data: bool=True) -> None:
        """Serialize the frame or some part of it into a file stream.

        Arguments:
            art_file: An open art file.
            header: Set to false if the header should not be written.
            data: Set to false if the frame data should not be written.
        """
        if header:
            header_data = _art_frame_header.getter(self)
            self.parser.pack_into_file(art_file, *header_data)
        if data:
            parser = FileStruct('<{}{}'.format(self.size, self.pixel_format))
            parser.pack_into_file(art_file, *self.data)
