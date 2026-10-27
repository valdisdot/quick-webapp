
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

    def __load_users(self) -> list[dict]:
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

    def __save_users(self, users: list[dict]):
        try:
            with open(self.__users_file, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=1)
        except Exception as e:
            raise UserDataSourceException("Unexpected error while saving users") from e

    def create_user(self, user: User, password: str) -> User:
        try:
            user_name = str(user.user_name)
            users = self.__load_users()

            if any(u.get("user_name") == user_name for u in users):
                raise UserDataSourceException("User already exists")

            record = {
                "user_name": user_name,
                "name": str(user.name) if getattr(user, "name", None) else None,
                "password": str(password),
                "locked": bool(getattr(user, "locked", False)),
                "active": bool(getattr(user, "active", True)),
                "requires_password_update": bool(getattr(user, "requires_password_update", False)),
                "roles": list(getattr(user, "roles", [])),
            }
            users.append(record)
            self.__save_users(users)

            return user
        except UserDataSourceException as e:
            raise e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while creating a user") from e

    def is_user_exist(self, user_name: str) -> bool:
        try:
            user_name = str(user_name)
            users = self.__load_users()
            return any(user.get("user_name") == user_name for user in users)
        except Exception as e:
            raise UserDataSourceException("Unexpected error while checking a username") from e

    def __load_user_record(self, user_name: str) -> dict:
        users = self.__load_users()
        for user in users:
            if user.get("user_name") == user_name:
                return user
        raise UserDataSourceException("User does not exist")

    def __save_user_record(self, record: dict):
        user_name = record.get("user_name")
        if not user_name:
            raise UserDataSourceException("User record missing user_name")
        users = self.__load_users()
        updated = False
        for i, user in enumerate(users):
            if user.get("user_name") == user_name:
                users[i] = record
                updated = True
                break
        if not updated:
            users.append(record)
        self.__save_users(users)

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
            record = self.__load_user_record(user_name)
            return User(
                user_name=record.get("user_name"),
                roles=record.get("roles", []),
                name=record.get("name"),
                locked=bool(record.get("locked", False)),
                active=bool(record.get("active", True)),
                requires_password_update=bool(record.get("requires_password_update", False)),
            )
        except UserDataSourceException as e:
            raise e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while fetching a user") from e

    def get_users(self, user_name_part: str, offset: int, limit: int, excluding_user_names: list[str] | None = None) -> list[User]:
        try:
            users = self.__load_users()
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
                result.append(
                    User(
                        user_name=record.get("user_name"),
                        roles=record.get("roles", []),
                        name=record.get("name"),
                        locked=bool(record.get("locked", False)),
                        active=bool(record.get("active", True)),
                        requires_password_update=bool(record.get("requires_password_update", False)),
                    )
                )

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

            record["name"] = str(user.name) if getattr(user, "name", None) else None
            record["locked"] = bool(getattr(user, "locked", False))
            record["active"] = bool(getattr(user, "active", True))
            record["requires_password_update"] = bool(getattr(user, "requires_password_update", False))
            record["roles"] = list(getattr(user, "roles", []))

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

            record["name"] = str(user.name) if getattr(user, "name", None) else None
            record["password"] = str(password)
            record["locked"] = bool(getattr(user, "locked", False))
            record["active"] = bool(getattr(user, "active", True))
            record["requires_password_update"] = bool(getattr(user, "requires_password_update", False))
            record["roles"] = list(getattr(user, "roles", []))

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
