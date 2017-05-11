from formats.helpers import FileStruct
from formats.fields import Fields

import io
from typing import Tuple, List
from enum import IntEnum
from collections import UserDict
import struct

import numpy as np

class ObjectKind(IntEnum):
    Object = 0x0001
    Prototype = 0xFFFF


class ObjectType(IntEnum):
    Wall = 0
    Portal = 1
    Container = 2
    Scenery = 3
    Projectile = 4
    Weapon = 5
    Ammo = 6
    Armor = 7
    Gold = 8
    Food = 9
    Scroll = 10
    Key = 11
    KeyRing = 12
    Written = 13
    Generic = 14
    Player = 15
    NPC = 16
    Trap = 17


class ObjectProperties(UserDict):
    parsers = (
        None,
        None,
        None,
        FileStruct("<H12B"), # 3
        FileStruct("<H16B"), # 4
        FileStruct("<H20B")  # 5
    )

    pro_parsers = (
        None,
        None,
        None,
        FileStruct("<12B"), # 3
        FileStruct("<16B"), # 4
        FileStruct("<20B")  # 5
    )

    # Mapping from type to tuple of all (field name, parser)
    type_fields = (
        Fields.wall_fields,
        Fields.portal_fields,
        Fields.container_fields,
        Fields.scenery_fields,
        Fields.projectile_fields,
        Fields.weapon_fields,
        Fields.ammo_fields,
        Fields.armor_fields,
        Fields.gold_fields,
        Fields.food_fields,
        Fields.scroll_fields,
        Fields.key_fields,
        Fields.key_ring_fields,
        Fields.written_fields,
        Fields.generic_fields,
        Fields.player_fields,
        Fields.npc_fields,
        Fields.trap_fields
    )

    # Size in bytes of included field flags.
    # len(Fields.type) / 32
    type_flags_length = (
        3, # 00 Wall
        3, # 01 Portal
        3, # 02 Container
        3, # 03 Scenery
        3, # 04 Projectile
        4, # 05 Weapon
        4, # 06 Ammo
        4, # 07 Armor
        4, # 08 Gold
        4, # 09 Food
        4, # 10 Scroll
        4, # 11 Key
        4, # 12 KeyRing
        4, # 13 Written
        4, # 14 Generic
        5, # 15 Player
        5, # 16 Critter
        3  # 17 Trap
    )

    @classmethod
    def read_from(cls, obj_file: io.FileIO, obj_type:ObjectType=None, prototype=False) -> "ObjectProperties":
        # raise NotImplementedError()

        properties = cls()
        if not prototype:
            field_count, *raw_flags = cls.parsers[cls.type_flags_length[obj_type]].unpack_from_file(obj_file)

        else:
            raw_flags = cls.pro_parsers[cls.type_flags_length[obj_type]].unpack_from_file(obj_file)
            

        flags = np.fliplr(np.unpackbits(np.array(raw_flags, dtype=np.uint8)).reshape(-1, 8)).flatten()

        if (not prototype and field_count != np.sum(flags)):
                raise RuntimeError("Field count doesn't match actual: %d versus %d" % (field_count, np.sum(flags)))

        # Parse fields from file
        for name, parser in cls.type_fields[obj_type]:
            properties[name] = parser.read_from(obj_file)

            # if name == "scripts" or name == "known_name":
            #     print(properties[name])

        return properties

    def write_to(self, obj_file: io.FileIO, obj_type:ObjectType=None, prototype=False):

        if not prototype:
            flags = []

            for name, parser in self.type_fields[obj_type]:
                if name in self:
                    flags.append(1)
                else:
                    flags.append(0)

            flags = np.array(flags)
            raw_flags = np.packbits(np.fliplr(flags.reshape(-1, 8)))

        else:
            raise NotImplementedError("Can not write prototype to file.")



class ObjectIdentifier(object):
    format = "G_{:08X}_{:04X}_{:04X}_{:04X}_{:012X}".format

    def __init__(self, raw_data):
        self.data = (
            int.from_bytes(raw_data[:4], 'little'),
            int.from_bytes(raw_data[4:6], 'little'),
            int.from_bytes(raw_data[6:8], 'little'),
            int.from_bytes(raw_data[8:10], 'big'),
            int.from_bytes(raw_data[10:], 'big'),
        )

    def __repr__(self):
        return self.format(*self.data)

    def __eq__(self, other):
        self.data == other.data

    def to_bytes(self) -> List[bytes]:

        # Perhaps better to just store the raw data during init.
        return (
            int.to_bytes(self.data[0], 4, 'little') +
            int.to_bytes(self.data[1], 2, 'little') +
            int.to_bytes(self.data[2], 2, 'little') +
            int.to_bytes(self.data[3], 2, 'big') +
            int.to_bytes(self.data[4], 6, 'big')
        )


class Object(object):
    Kind = ObjectKind
    Type = ObjectType
    Properties = ObjectProperties
    Identifier = ObjectIdentifier

    version_format = "<I"
    version_parser = FileStruct(version_format)
    valid_version = 119

    # First 2 bytes specify what kind of object is being described, either
    # prototype or normal
    kind_format = "H"
    kind = ObjectKind.Object

    # .mob files:
    unknown_data_format = "6s"
    prototype_format = "I"
    unknown_data2_format = "20s"
    raw_identifier_format = "16s"  # matches file name, unique per entity per map
    raw_type_format = "I"  # If that does not fail reads 2 more bytes

    full_format = "<" + "".join((kind_format, unknown_data_format,
                                 prototype_format, unknown_data2_format,
                                 raw_identifier_format, raw_type_format))
    full_parser = FileStruct(full_format)

    def __init__(self, version: int, prototype: int, type: ObjectType, identifier: ObjectIdentifier,
                 properties: ObjectProperties):

        self.version = version
        self.prototype = prototype
        self.type = type
        self.identifier = identifier
        self.properties = properties

    @classmethod
    def read_from(cls, obj_file: io.FileIO) -> "Object":

        version, = cls.version_parser.unpack_from_file(obj_file)

        if (version != cls.valid_version):
            raise TypeError("Arkanum does not support object version %d" % version)

        kind, _, prototype, _2, raw_identifier, raw_type = cls.full_parser.unpack_from_file(obj_file)

        type = Object.Type(raw_type)

        if kind == cls.Kind.Prototype:
            properties = Object.Properties.read_from(obj_file, obj_type=type, prototype=True)
            return Prototype(version=version,
                             prototype=prototype,
                             type=type,
                             identifier=ObjectIdentifier(raw_identifier),
                             properties=properties)

        elif kind == cls.Kind.Object:

            properties = Object.Properties.read_from(obj_file, obj_type=type)

            return Object(version=version,
                          prototype=prototype,
                          type=type,
                          identifier=Object.Identifier(raw_identifier),
                          properties=properties)

    def write_to(self, obj_file: io.FileIO) -> None:

        self.version_parser.pack_into_file(obj_file, self.valid_version)

        self.full_parser.pack_into_file(obj_file, self.kind, (b'\x00'*6), self.prototype, (b'\x00'*20), self.identifier.to_bytes(), self.type)

        self.properties.write_to(obj_file, obj_type=self.type, prototype=self.kind==ObjectKind.Prototype)

class Prototype(Object):
    kind = ObjectKind.Prototype

    @classmethod
    def read(cls, pro_file_path: str) -> "Prototype":

        with open(pro_file_path, "rb") as pro_file:

            pro = cls.read_from(pro_file)
            pro.file_path = pro_file_path

            return pro

    def write(self, pro_file_path: str) -> None:

        with open(pro_file_path, "wb") as pro_file:

            self.write_to(pro_file)
