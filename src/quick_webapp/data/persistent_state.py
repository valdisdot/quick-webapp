from pathlib import Path
import json
import copy
from typing import Any

class PersistentState:
    """
    Utility class for storing the state of any object with an option to save it persistently as JSON.
    The current implementation saves objects in the .state/<name>.json file.
    """

    __STATE_DIR_NAME = ".state"

    def __init__(self, name: str, strict=False):
        """
        Constructor creates the .state directory (if it doesn't exist) and loads <name>.json.
        If strict is True, raises ValueError on errors (missing JSON file, read errors, etc.),
        otherwise initializes with an empty object.
        """

        self.__name = name

        if name is None or not len(name.strip()):
            raise ValueError("State name is not specified or is empty!")
        else:
            Path(self.__STATE_DIR_NAME).mkdir(exist_ok=True)
            self.__state_path = Path(self.__STATE_DIR_NAME) / f"{name}.json"
            error = None

            try:
                if self.__state_path.exists():
                    with open(self.__state_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                        if isinstance(data, dict):
                            self.__object = data
                        else:
                            error = (
                                f"State '{name}' is not an object in {self.__state_path}!"
                            )
                else:
                    error = f"State '{name}' is missing at {self.__state_path}!"
            except FileNotFoundError:
                error = f"State '{name}' is missing at {self.__state_path}!"
            except json.JSONDecodeError as e:
                error = f"State '{name}' is not a JSON object in {self.__state_path}!"
            except Exception as e:
                error = f"Error building state '{name}' ({e}) from {self.__state_path}!"

            if error:
                if strict:
                    raise ValueError(error)
                else:
                    self.__object = {}

    def get_storage(self, clone = False) -> dict[Any]:
        """
        Returns the state object.
        If clone is True, returns a copy of the object outside of persistence.
        """

        return copy(self.__object) if clone else self.__object

    def contains_key(self, key: Any):
        """
        Checks if the key exists in the state object.
        """
        return key in self.__object

    def acquire_value(self, key: Any, alter: Any = None) -> Any:
        """
        Returns the value for the given key from the internal object, or alter if the key is missing.
        If the key is missing and alter is not None, sets alter as the value in the internal object.
        """
        if key in self.__object:
            return self.__object[key]
        else:
            if alter is not None: 
                self.__object[key] = alter
            return alter

    def put_value(self, key: Any, value: Any):
        """
        Sets the value for the given key.
        """

        self.__object[key] = value

    def update_storage(self, object: dict[Any], strict = False):
        """
        Updates the state object with values from another object.
        If strict is True and the provided object is not a dict, raises ValueError.
        """

        if isinstance(object, dict):
            self.__object.update(object)
        elif strict:
            raise ValueError("Update object is not a dictionary")

    def persist_state(self):
        """
        Saves the state object to persistent storage.
        Raises ValueError on save errors.
        """

        try:
            with open(self.__state_path, "w", encoding="utf-8") as f:
                json.dump(self.__object, f)
        except Exception as e:
            raise ValueError(f"Error saving state '{self.__name}' to {self.__state_path} ({e})")

    def __str__(self):
        return str(self.__object)
