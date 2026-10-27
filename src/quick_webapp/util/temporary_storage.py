from pathlib import Path
import shutil
from uuid import uuid4
import io

class TemporaryStorage:
    """
    Utility class for temporary file storage.
    Current implementation stores files in .temp/<uuid>.
    """

    __TEMP_DIR = Path(".temp")

    def __init__(self):
        self.__TEMP_DIR.mkdir(exist_ok=True)
        self.__registry: dict[str, str] = {}

    def contains_binary(self, name: str) -> bool:
        """
        Deletes all temporary files and clears the registry.
        """

        if name not in self.__registry:
            return False

        path = Path(self.__TEMP_DIR) / self.__registry[name]
        return path.exists() and path.is_file()

    def write_binary(self, name: str, binary: bytes | io.BytesIO):
        """
        Stores binary data in the temporary storage.
        """

        file_id = str(uuid4())
        self.__registry[name] = file_id

        path = Path(self.__TEMP_DIR) / file_id

        if isinstance(binary, io.BytesIO):
            data = binary.getvalue()
        else:
            data = binary

        with open(path, "wb") as f:
            f.write(data)

    def read_binary_as_stream(self, name: str) -> io.BytesIO:
        """
        Reads binary data from temporary storage as a data stream.
        """

        if name not in self.__registry:
            raise FileNotFoundError(f"{name} not found in storage")

        path = Path(self.__TEMP_DIR) / self.__registry[name]

        with open(path, "rb") as f:
            return io.BytesIO(f.read())

    def read_binary_as_bytes(self, name: str) -> bytes:
        """
        Reads binary data from temporary storage as bytes.
        """

        if name not in self.__registry:
            raise FileNotFoundError(f"{name} not found in storage")

        path = Path(self.__TEMP_DIR) / self.__registry[name]

        with open(path, "rb") as f:
            return f.read()

    def delete_binary(self, name: str):
        """
        Deletes file if present, do nothing otherwise.
        """

        file_id = self.__registry.pop(name, None)
        if file_id is None:
            return

        path = self.__TEMP_DIR / file_id

        try:
            path.unlink()
        except FileNotFoundError:
            pass
        
    def delete_all(self):
        """
        Deletes all temporary files and clears the registry.
        """
        
        if self.__TEMP_DIR.exists():
            shutil.rmtree(self.__TEMP_DIR, ignore_errors=True)

        self.__registry.clear()