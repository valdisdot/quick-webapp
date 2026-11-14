from abc import ABC, abstractmethod
from quick_webapp.security.basic.user import User
import sqlite3

class UserDataSourceException(Exception):
    """
    Exception for user data source layer.
    """

    def __init__(self, *args, **kvargs):
        super().__init__(*args, **kvargs)

class UserDataSource(ABC):
    """
    Abstract data source layer to perform CRUD to User records.
    """

    @abstractmethod
    def create_user(user: User, password: str) -> User:
        """
        Creates a user from the User record.
        """
        pass

    @abstractmethod
    def is_user_exist(self, user_name: str) -> bool:
        """
        Checks if the user exists.
        """
        pass

    @abstractmethod
    def get_user_password(self, user_name: str) -> str:
        """
        Fetches user password.
        """
        pass

    @abstractmethod
    def get_user(self, user_name: str) -> User | None:
        """
        Fetches User record.
        """
        pass

    def get_users(self, user_name_part: str, offset: int, limit: int, excluding_user_names: list[str] | None = None) -> list[User]:
        """
        Fetches Users that have user_name like user_name_part with offset and limit.
        """
        pass

    @abstractmethod
    def update_user_lock(self, user_name: str, lock: bool):
        """
        Locks/unlocks the user.
        """
        pass
          
    @abstractmethod
    def update_user(user: User) -> User:
        """
        Updates existing user info.
        """
        pass

    @abstractmethod
    def save_user(user: User, password: str) -> User:
        """
        Saves existing user info and password.
        """
        pass

    @abstractmethod
    def get_roles(self) -> list[str]:
        """
        Fetches a list with all user roles.
        """
        pass

class LocalUserDataSource(UserDataSource):
    """
    Minimal implementation of UserDataSource.

    Uses SQLite database file to store the user data.
    """

    def __init__(self, predefined_roles: list[str], db_path="users.db"):
        self.__connection = sqlite3.connect(db_path, check_same_thread=False)
        self.__connection.autocommit = False
        self.__connection.row_factory = sqlite3.Row
        self.__ensure_table(predefined_roles)
    
    def __del__(self):
        self.__connection.close()

    def __ensure_table(self, predefined_roles: list[str]):
        try:
            self.__connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user (
                    user_name TEXT PRIMARY KEY,
                    is_ui_user INTEGER NOT NULL,
                    is_service_user INTEGER NOT NULL,
                    name TEXT,
                    password TEXT NOT NULL,
                    locked INTEGER NOT NULL,
                    active INTEGER NOT NULL,
                    requires_password_update INTEGER NOT NULL
                )
                """
            )
            self.__connection.execute(
                """
                CREATE TABLE IF NOT EXISTS role (
                    name TEXT PRIMARY KEY
                )
                """
            )
            self.__connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_role (
                    user_name TEXT,
                    role TEXT,
                    FOREIGN KEY(user_name) REFERENCES user(user_name),
                    FOREIGN KEY(role) REFERENCES role(name),
                    PRIMARY KEY(user_name, role)
                )
                """
            )

            for role in predefined_roles:
                self.__connection.execute("INSERT OR IGNORE INTO role (name) VALUES (?)", (role,))

            self.__connection.commit()
        except sqlite3.DatabaseError as e:
            raise UserDataSourceException("Database error while initializing user-related tables") from e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while initializing user-related tables") from e  

    def create_user(self, user: User, password: str) -> User:
        try:
            user_name = str(user.user_name)
            password = str(password)
            self.__connection.execute(
                "INSERT INTO user (user_name, is_ui_user, is_service_user, name, password, locked, active, requires_password_update) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_name,
                    int(user.is_ui_user),
                    int(user.is_service_user),
                    user.name if user.name else None,
                    password,
                    int(user.locked),
                    int(user.active),
                    int(user.requires_password_update),
                ),
            )

            for role in user.roles:
                role = str(role)
                self.__connection.execute(
                    "INSERT INTO user_role (user_name, role) VALUES (?, ?)",
                    (user_name, role),
                )
            self.__connection.commit()
            return user
        
        except sqlite3.IntegrityError as e:
            self.__connection.rollback()
            raise UserDataSourceException("Constraint error while creating a user") from e
        except sqlite3.DatabaseError as e:
            raise UserDataSourceException("Database error while creating a user") from e
        except Exception as e:
            self.__connection.rollback()
            raise UserDataSourceException("Unexpected error while creating a user") from e

    def is_user_exist(self, user_name: str) -> bool:
        try:
            user_name = str(user_name)
            cur = self.__connection.execute("SELECT 1 FROM user WHERE user_name = ?", (user_name,))
            return cur.fetchone() is not None
        except sqlite3.DatabaseError as e:
            raise UserDataSourceException(f"Database error while checking a username") from e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while checking a username") from e
        
    def get_user_password(self, user_name: str) -> str:
        try:
            user_name = str(user_name)
            cur = self.__connection.execute("SELECT password FROM user WHERE user_name = ?", (user_name,))
            row = cur.fetchone()
            if not row:
                return UserDataSourceException("User does not exist")
            
            return row["password"]
        
        except sqlite3.DatabaseError as e:
            raise UserDataSourceException(f"Database error while fetching a username password") from e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while fetching a username password") from e

    def get_user(self, user_name: str) -> User:
        try:
            user_name = str(user_name)
            cur = self.__connection.execute("SELECT * FROM user WHERE user_name = ? LIMIT 1", (user_name,))
            row = cur.fetchone()
            if not row:
                return UserDataSourceException("User does not exist")
            
            roles_cur = self.__connection.execute(
                "SELECT DISTINCT role FROM user_role WHERE user_name = ?", (user_name,)
            )
            roles = [r["role"] for r in roles_cur.fetchall()]
            return User(
                user_name=row["user_name"],
                is_ui_user=row["is_ui_user"],
                is_service_user=row["is_service_user"],
                roles=roles,
                name=row["name"],
                locked=bool(row["locked"]),
                active=bool(row["active"]),
                requires_password_update=bool(row["requires_password_update"]),
            )
        
        except sqlite3.DatabaseError as e:
            raise UserDataSourceException(f"Database error while fetching a user") from e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while fetching a user") from e

    def get_users(self, user_name_part: str, offset: int, limit: int, excluding_user_names: list[str] | None = None) -> list[User]:
        try:
            part = (user_name_part or "")
            params: list[object] = []
            where_clauses: list[str] = []

            if part:
                where_clauses.append("user_name LIKE ?")
                params.append(f"%{part}%")

            if excluding_user_names:
                excluded = [str(u) for u in excluding_user_names if u is not None and len(str(u))]
                if excluded:
                    placeholders = ",".join(["?"] * len(excluded))
                    where_clauses.append(f"user_name NOT IN ({placeholders})")
                    params.extend(excluded)

            where_sql = ""
            if where_clauses:
                where_sql = " WHERE " + " AND ".join(where_clauses)

            query = f"SELECT * FROM user {where_sql} ORDER BY user_name LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cur = self.__connection.execute(query, tuple(params))
            rows = cur.fetchall()

            users: list[User] = []
            for row in rows:
                user_name = row["user_name"]
                roles_cur = self.__connection.execute(
                    "SELECT DISTINCT role FROM user_role WHERE user_name = ?",
                    (user_name,),
                )
                roles = [r["role"] for r in roles_cur.fetchall()]

                users.append(
                    User(
                        user_name=row["user_name"],
                        is_ui_user=row["is_ui_user"],
                        is_service_user=row["is_service_user"],
                        roles=roles,
                        name=row["name"],
                        locked=bool(row["locked"]),
                        active=bool(row["active"]),
                        requires_password_update=bool(row["requires_password_update"]),
                    )
                )

            return users

        except sqlite3.DatabaseError as e:
            raise UserDataSourceException("Database error while fetching users") from e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while fetching users") from e

    def update_user_lock(self, user_name: str, lock: bool):
        try:
            self.__connection.execute("UPDATE user SET locked = ? WHERE user_name = ?", (int(lock), str(user_name)))
            self.__connection.commit()
        except sqlite3.DatabaseError as e:
            raise UserDataSourceException(f"Database error while updating a user lock") from e
        except Exception as e:
            self.__connection.rollback()
            raise UserDataSourceException("Unexpected error while updating a user lock") from e
        
    def update_user(self, user: User) -> User:
        try:
            user_name = str(user.user_name)
            self.__connection.execute(
                "UPDATE user SET is_ui_user = ?, is_service_user = ?, name = ?, locked = ?, active = ?, requires_password_update = ? WHERE user_name = ?",
                (
                    int(user.is_ui_user), 
                    int(user.is_service_user),
                    str(user.name) if user.name else None,
                    int(user.locked),
                    int(user.active),
                    int(user.requires_password_update),
                    user_name
                )
            )
            
            self.__connection.execute(
                "DELETE FROM user_role WHERE user_name = ?", (user_name,)
            )
            for role in user.roles:
                role = str(role)
                self.__connection.execute(
                    "INSERT INTO user_role (user_name, role) VALUES (?, ?)",
                    (user_name, role),
                )
            self.__connection.commit()
            return user
        
        except sqlite3.IntegrityError as e:
            self.__connection.rollback()
            raise UserDataSourceException("Constraint error while saving a user") from e
        except sqlite3.DatabaseError as e:
            raise UserDataSourceException(f"Database error while saving a user") from e
        except Exception as e:
            self.__connection.rollback()
            raise UserDataSourceException("Unexpected error while saving a user") from e

    def save_user(self, user: User, password: str) -> User:
        try:
            user_name = str(user.user_name)
            password = str(password)
            self.__connection.execute(
                "UPDATE user SET is_ui_user = ?, is_service_user = ?, name = ?, password = ?, locked = ?, active = ?, requires_password_update = ? WHERE user_name = ?",
                (
                    int(user.is_ui_user),
                    int(user.is_service_user),
                    str(user.name) if user.name else None,#is_ui_user, is_service_user
                    password,
                    int(user.locked),
                    int(user.active),
                    int(user.requires_password_update),
                    user_name
                )
            )
            
            self.__connection.execute(
                "DELETE FROM user_role WHERE user_name = ?", (user_name,)
            )
            for role in user.roles:
                role = str(role)
                self.__connection.execute(
                    "INSERT INTO user_role (user_name, role) VALUES (?, ?)",
                    (user_name, role),
                )
            self.__connection.commit()
            return user
        
        except sqlite3.IntegrityError as e:
            self.__connection.rollback()
            raise UserDataSourceException("Constraint error while saving a user") from e
        except sqlite3.DatabaseError as e:
            raise UserDataSourceException(f"Database error while saving a user") from e
        except Exception as e:
            self.__connection.rollback()
            raise UserDataSourceException("Unexpected error while saving a user") from e

    def get_roles(self) -> list[str]:
        try:            
            roles_cur = self.__connection.execute("SELECT DISTINCT name FROM role")
            return [row["name"] for row in roles_cur.fetchall()]

        except sqlite3.DatabaseError as e:
            raise UserDataSourceException(f"Database error while fetching a user") from e
        except Exception as e:
            raise UserDataSourceException("Unexpected error while fetching a user") from e
