import sqlite3
from quick_webapp.auth.basic.user import User
from quick_webapp.auth.basic.data_source import UserDataSource, UserDataSourceException

class SQLiteUserDataSource(UserDataSource):
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
                "INSERT INTO user (user_name, name, password, locked, active, requires_password_update) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_name,
                    str(user.name) if user.name else None,
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

    def update_user_lock(self, user_name: str, lock: bool):
        try:
            self.__connection.execute(
                "UPDATE user SET locked = ? WHERE user_name = ?", (int(lock), str(user_name))
            )
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
                "UPDATE user SET name = ?, locked = ?, active = ?, requires_password_update = ? WHERE user_name = ?",
                (
                    str(user.name) if user.name else None,
                    int(user.locked),
                    int(user.active),
                    int(user.requires_password_update),
                    user_name,
                ),
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
                "UPDATE user SET name = ?, password = ?, locked = ?, active = ?, requires_password_update = ? WHERE user_name = ?",
                (
                    str(user.name) if user.name else None,
                    password,
                    int(user.locked),
                    int(user.active),
                    int(user.requires_password_update),
                    user_name,
                ),
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
