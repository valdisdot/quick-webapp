from abc import ABC, abstractmethod
from quick_webapp.security.basic.user import User

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