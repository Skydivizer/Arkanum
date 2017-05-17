from os import path
from glob import glob

from formats.map.sec import Sector
from formats.obj import Prototype
from formats.obj import count
from formats.map.mob import MobileObject

from typing import List, Callable, Any
import tempfile

# base_paths = glob(r"D:\Games\Arcanum")
base_paths = glob("/home/sebastian/.wine/drive_c/GOG Games/Arcanum/")


def validate_files(directory: str, validated_objects: List[Sector], extension: str, validator_function: Callable[[str], Any], verbose=True):

    template = path.join(directory, "*")

    for file_path in glob(template):

        if path.isdir(file_path):
            validate_files(file_path, validated_objects, extension, validator_function, verbose)

        elif file_path.lower().endswith(extension):
            if verbose:
                print("Validating %s.." % file_path)
            validated_object = validator_function(file_path)
            validated_objects.append(validated_object)


def main():

    validated_objects = []  # type: List[Terrain]

    for base_path in base_paths:
        validate_files(base_path, validated_objects, ".sec", Sector.read)
        validate_files(base_path, validated_objects, ".mob", MobileObject.read)
        validate_files(base_path, validated_objects, ".pro", Prototype.read)

    print(flush=True)

    tmp_path = tempfile.mkstemp()[1]

    for validated_object in validated_objects:

        print("Further validation of %s.." % validated_object.file_path, flush=True)
        validated_object.write(tmp_path)

    


if __name__ == "__main__":
    main()
