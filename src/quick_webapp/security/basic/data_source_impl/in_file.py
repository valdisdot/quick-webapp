
from typing import Any
import json
import os
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.data_source import UserDataSource, UserDataSourceException

class InFileUserDataSource(UserDataSource):
    """
    File-based implementation using JSON files.

    Layout under dir_path:
    - roles.json  -> JSON array of role names
    - users.json  -> JSON array of users
    """
            
    def __init__(self, predefined_roles: list[str], dir_path: str = "users"):
        self.__root_dir = dir_path
        self.__roles_file = os.path.join(self.__root_dir, "roles.json")
        self.__users_file = os.path.join(self.__root_dir, "users.json")

        try:
            os.makedirs(self.__root_dir, exist_ok=True)
            existing_roles: list[str] = []
            if os.path.exists(self.__roles_file):
                try:
                    with open(self.__roles_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            existing_roles = [str(r) for r in data]
                except json.JSONDecodeError:
                    existing_roles = []

            merged_roles: list[str] = []
            seen: set[str] = set()
            for role in (existing_roles + list(predefined_roles or [])):
                r = str(role)
                if r not in seen:
                    seen.add(r)
                    merged_roles.append(r)

            with open(self.__roles_file, "w", encoding="utf-8") as f:
                json.dump(merged_roles, f)

        except Exception as e:
            raise UserDataSourceException("Failed to initialize file-based user storage") from e

    def __load_user_records(self) -> list[dict]:
        if not os.path.exists(self.__users_file):
            return []
        try:
            with open(self.__users_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError as e:
            raise UserDataSourceException("Corrupted users data") from e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while loading users") from e

    def __load_user_record(self, user_name: str) -> dict:
        users = self.__load_user_records()
        for user in users:
            if user.get("user_name") == user_name:
                return user
        raise UserDataSourceException("User does not exist")

    def __write_user_records(self, records: list[dict]):
        try:
            with open(self.__users_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=1)
        except Exception as e:
            raise UserDataSourceException("Unexpected error while saving users") from e

    def __save_user_record(self, record: dict):
        user_name = record.get("user_name")
        if not user_name:
            raise UserDataSourceException("User record missing user_name")
        users = self.__load_user_records()
        updated = False
        for i, user in enumerate(users):
            if user.get("user_name") == user_name:
                users[i] = record
                updated = True
                break
        if not updated:
            users.append(record)
        self.__write_user_records(users)

    @staticmethod
    def __serialize_user(user: User, user_name: str, password: str) -> dict[str, Any]:
        return {
            "user_name": user_name,
            "is_ui_user": user.is_ui_user,
            "is_service_user": user.is_service_user,
            "name": user.name,
            "password": password,
            "locked": user.locked,
            "active": user.active,
            "requires_password_update": user.requires_password_update,
            "roles": user.roles
        }

    @staticmethod
    def __deserialize_user(record: dict[str, Any]) -> User:
        return User(
            user_name=record.get("user_name"),
            is_ui_user=record.get("is_ui_user"),
            is_service_user=record.get("is_service_user"),
            roles=record.get("roles"),
            name=record.get("name"),
            locked=record.get("locked"),
            active=record.get("active"),
            requires_password_update=record.get("requires_password_update")
        )

    def create_user(self, user: User, password: str) -> User:
        try:
            user_name = str(user.user_name)
            user_records = self.__load_user_records()

            if any(record.get("user_name") == user_name for record in user_records):
                raise UserDataSourceException("User already exists")

            user_records.append(self.__serialize_user(user, user_name, str(password)))
            self.__write_user_records(user_records)

            return user
        except UserDataSourceException as e:
            raise e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while creating a user") from e

    def is_user_exist(self, user_name: str) -> bool:
        try:
            user_name = str(user_name)
            return any(user_record.get("user_name") == user_name for user_record in self.__load_user_records())
        except Exception as e:
            raise UserDataSourceException("Unexpected error while checking a username") from e

    def get_user_password(self, user_name: str) -> str:
        try:
            user_name = str(user_name)
            record = self.__load_user_record(user_name)
            return record.get("password")
        except UserDataSourceException as e:
            raise e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while fetching a username password") from e

    def get_user(self, user_name: str) -> User | None:
        try:
            user_name = str(user_name)
            return self.__deserialize_user(self.__load_user_record(user_name))
        except UserDataSourceException as e:
            raise e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while fetching a user") from e

    def get_users(self, user_name_part: str, offset: int, limit: int, excluding_user_names: list[str] | None = None) -> list[User]:
        try:
            users = self.__load_user_records()
            part = (user_name_part or "").lower()

            if excluding_user_names is None:
                excluding_user_names = []

            if part:
                users = [
                    user for user in users
                    if part in str(user.get("user_name", "")).lower() and str(user.get("user_name", "")).lower() not in excluding_user_names
                ]

            users.sort(key=lambda u: str(u.get("user_name", "")))
            window = users[offset: offset + limit]

            result: list[User] = []
            for record in window:
                result.append(self.__deserialize_user(record))

            return result
        
        except UserDataSourceException as e:
            raise e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while fetching users") from e

    def update_user_lock(self, user_name: str, lock: bool):
        try:
            user_name = str(user_name)
            record = self.__load_user_record(user_name)
            record["locked"] = lock
            self.__save_user_record(record)
        except UserDataSourceException as e:
            raise e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while updating a user lock") from e

    def update_user(self, user: User) -> User:
        try:
            user_name = str(user.user_name)
            record = self.__load_user_record(user_name)

            record["is_ui_user"] = user.is_ui_user
            record["is_service_user"] = user.is_service_user
            record["name"] = user.name
            record["locked"] = user.locked
            record["active"] = user.active
            record["requires_password_update"] = user.requires_password_update
            record["roles"] = user.roles

            self.__save_user_record(record)
            return user
        except UserDataSourceException as e:
            raise e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while saving a user") from e

    def save_user(self, user: User, password: str) -> User:
        try:
            user_name = str(user.user_name)
            record = self.__load_user_record(user_name)

            record["is_ui_user"] = user.is_ui_user
            record["is_service_user"] = user.is_service_user
            record["name"] = user.name
            record["password"] = password
            record["locked"] = user.locked
            record["active"] = user.active
            record["requires_password_update"] = user.requires_password_update
            record["roles"] = user.roles

            self.__save_user_record(record)
            return user
        except UserDataSourceException as e:
            raise e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while saving a user") from e

    def get_roles(self) -> list[str]:
        try:
            if not os.path.exists(self.__roles_file):
                return []
            with open(self.__roles_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(r) for r in data]
                return []
        except json.JSONDecodeError as e:
            raise UserDataSourceException("Corrupted roles data") from e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while fetching roles") from e
