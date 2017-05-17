from formats.obj import Object

class MobileObject(Object):
    """
    An object that is expected to "change" during play, e.g it moves or it can be picked up by the
    player or some critter. In the file format it seems to be defined as any other object.
    """
    def __init__(self, raw_object, file_path):
        super(MobileObject, self).__init__(
            version=raw_object.version,
            prototype=raw_object.prototype,
            type=raw_object.type,
            identifier=raw_object.identifier,
            properties=raw_object.properties,
            unknown=raw_object.unknown)
        self.file_path = file_path

    @classmethod
    def read(cls, mob_file_path: str) -> "MobileObject":

        with open(mob_file_path, "rb") as mob_file:

            rob = cls.read_from_raw(mob_file)

            return cls(rob, mob_file_path)

    def write(self, mob_file_path: str) -> None:

        with open(mob_file_path, "wb") as mob_file:

            self.write_to(mob_file)
