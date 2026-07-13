from collections.abc import Callable, Iterable
from uuid import uuid4
import time
import streamlit as st
from quick_webapp.auth.basic.user import User
from quick_webapp.auth.basic.data_source import UserDataSource, UserDataSourceException


class UserLayerException(Exception):
    """Common user layer related exception."""


class UserNotFoundException(UserLayerException):
    """Exception-indicator of user's absence."""


class PasswordNotMatchException(UserLayerException):
    """Exception-indicator of user's password checking fail."""


class PasswordToBeSetException(UserLayerException):
    """Exception-indicator that user must set the password to work with the application."""


class UserNotActiveException(UserLayerException):
    """Exception-indicator of user's inactivity."""


class UserLockedException(UserLayerException):
    """Exception-indicator of user being locked."""


class InvalidUserDataException(UserLayerException):
    """Exception for user record validation errors."""


class InvalidUserSessionException(UserLayerException):
    """Exception-indicator of user's session is invalid."""

class UserSession:
    """
    User session record class.
    """

    def __init__(self,
                 expires_at: int,
                 locale: str,
                 timezone: str, 
                 user: User
    ):
        self.__expires_at: int = expires_at
        self.__locale = locale
        self.__timezone = timezone
        self.__user: User = user
     
    @property
    def expires_at(self) -> int:
        """
        Expiration timestamp in seconds.
        """

        return self.__expires_at
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.__expires_at
    
    @property
    def locale(self) -> str:
        """
        User locale string.
        """

        return self.__locale

    @property
    def timezone(self) -> str:
        """
        User timezone string.
        """
                
        return self.__timezone
    
    @property
    def user(self) -> User:
        """
        User record of this session.
        """

        return self.__user
    
    def is_valid(self, locale: str, timezone: str):
        """
        Check is session is valid now.
        """

        time.time() > self.__expires_at and self.__locale == locale and self.__timezone == timezone

class UserService:
    """
    Service layer class to maintain user-password based authorization.
    The service must be initialized with constructor, where user provides data source, password hash gen/check function, validators and constants.
    Methods may return string with session ID (so UI related flow store it in cache), a User object (to display/edit the user) and bool checks.

    Direct user method:

    - check_user_credentials(user_name: str, password: str) to check user-password pair without getting a User record
    - login(user_name: str, password: str, user_locale: str, user_timezone: str) to login the user, returns a session id
    - get_user(session_id: str, user_locale: str, user_timezone: str) to get a User object
    - set_password(session_id: str, password: str, new_password: str, user_locale: str, user_timezone: str) to set the current user password and relogin with a new one, returns a session id
    - is_logged_in(session_id: str, user_locale: str, user_timezone: str) checks if the user logged in
    - is_new_password_update_required(session_id: str, user_locale: str, user_timezone: str) checks if user must set a new password
    - is_allowed(session_id: str, with_role: list[str] | str) checks if the user has the role in their roles
    - logout(session_id: str) to logout the current user
    
    Common user methods:

    - fetch_user(user_name: str) to simple fetch the user from data storage
    - register_user(user: User, password: str) to create a User, returns a User object that was returns from the UserDataSource
    - update_user(user: User, password: str | None = None) to edit/update a User, returns a User object that was returns from the UserDataSource
    - lock_user(user_name: str) and unlock_user(user_name: str) methods
    - close_user_sessions(user_name: str) to close all sessions by the username
    - get_user_sessions(user_name: str) TBD
    - get_all_user_sessions() TBD

    Service methods:

    - get_roles() to fecth a list with all available roles 
    - clear_expired_sessions() to free resources by deleting expired session records.
    - validate_user_name(self, user_name: str) check
    - validate_password(self, password: str) check
    - properties max_login_attempts and session_lifespan_seconds

    """

    def __init__(self,
                 user_data_source: UserDataSource,
                 password_hash_function: Callable[[str], str],
                 password_hash_check_function: Callable[[str, str], bool],
                 max_login_attempts = 3,
                 user_name_validator: Callable[[str], bool] = lambda user_name: user_name is not None and len(user_name),
                 password_validator: Callable[[str], bool] = lambda passsword: passsword is not None and len(passsword) > 4,
                 session_lifespan_seconds = 3600
    ):
        self.__user_data_source: UserDataSource = user_data_source
        self.__password_hash_function: Callable[[str], str] = password_hash_function
        self.__password_hash_check_function : Callable[[str, str], bool] = password_hash_check_function
        self.__max_login_attempts: int = max_login_attempts
        self.__user_name_validator: Callable[[str], bool] = user_name_validator
        self.__password_validator: Callable[[str], bool] = password_validator
        self.__session_lifespan_seconds = session_lifespan_seconds
        # user_name: list[session_id]
        self.__user_session_registry: dict[str, list[str]] = {}
        # session_id: UserSession
        self.__sessions: dict[str, UserSession] = {}
        self.__login_attempts: dict[str, int] = {}

    def __check_user_credentials(self, user_name: str, password: str) -> bool:

            used_login_attempts = self.__login_attempts.get(user_name, 0)
            if used_login_attempts >= self.__max_login_attempts:
                raise UserLockedException(f"User '{user_name}' has exceeded {self.__max_login_attempts} login attempts")
    
            if not self.__password_hash_check_function(password, self.__user_data_source.get_user_password(user_name)):
                used_login_attempts += 1
                self.__login_attempts[user_name] = used_login_attempts
                if used_login_attempts >= self.__max_login_attempts:
                    self.update_user_lock(user_name)
                    raise UserLockedException(f"User '{user_name}' has been locked")
                return False
            return True

    def login(self, user_name: str, password: str, user_locale: str, user_timezone: str) -> str:
        """
        Logins the user and set the session. Returns a session ID if user allowed to login.
        If user exceeds max_login_attempts, user will be locked.

        Raises: UserLockedException, PasswordNotMatchException, UserNotFoundException and common UserLayerException
        """
            
        if user_name is None or not len(user_name):
            raise UserLayerException("User name is empty")
            
        if password is None or not len(password):
            raise UserLayerException("User password is empty")
            
        try:
            if not self.__user_data_source.is_user_exist(user_name):
                raise UserNotFoundException(f"User '{user_name}' is not found")
                
            if not self.__check_user_credentials(user_name, password):
                raise PasswordNotMatchException(f"Incorrect password for user '{user_name}'")
                
            user = self.__user_data_source.get_user(user_name)

            if not user.active:
                raise UserNotActiveException(f"User '{user_name}' is not active")
            if user.locked:
                raise UserLockedException(f"User '{user_name}' is locked")
                
            session_id = self.__make_session_id()
            
            user_session = UserSession(time.time() + self.__session_lifespan_seconds, user_locale, user_timezone, user)
            self.__sessions[session_id] = user_session
            self.__login_attempts[user_name] = 0
                
            if user_name not in self.__user_session_registry:
                sessions = []
                sessions.append(session_id)
                self.__user_session_registry[user_name] = sessions
            else:
                self.__user_session_registry[user_name].append(session_id)

            return session_id

        except UserLayerException as e:
            raise e
        except UserDataSourceException as e:
            raise UserLayerException(e) from e
        except Exception as e:
            raise UserLayerException("Unexpected error during login") from e

    def is_logged_in(self, session_id: str, user_locale: str, user_timezone: str) -> bool:
        """
        Checks if the user is logged in and it session is valid.
        """

        if session_id and session_id in self.__sessions:
            user_session = self.__sessions.get(session_id)
            if not user_session.is_valid(user_locale, user_timezone):
                user = user_session.user
                return user.active and not user.locked
        return False
    
    def is_new_password_update_required(self, session_id: str) -> bool:
        """
        Checks if the session user must update the password. Only session_id is required.
        """

        if session_id and session_id in self.__sessions:
            user = self.__sessions.get(session_id).user
            return user.requires_password_update
        return False
    
    def is_allowed(self, session_id: str, with_roles: str | list[str]) -> bool:
        """
        Checks if the user has the role in their roles. Only session_id is required.
        
        If with_role is null/empty or element of the with_role contains not string, returns False.
        """

        return (
            with_roles and 
            len(with_roles) and 
            session_id and 
            session_id in self.__sessions and
            self.__sessions.get(session_id).user.has_roles(with_roles)
        )

    def set_password(self, session_id: str, password: str, new_password: str, user_locale: str, user_timezone: str) -> str:
        """
        Sets tne current user password, clears all sessions and relogins, returning a new session id.
        Password policy as the same as for login - user will be locked if the current password does not match max_login_attempts.
        User property requires_password_update after successfull password set will be False.
        User state policy also the same - user will able to set password but for unlock/making active, use update_user()

        Raises: InvalidUserSessionException, UserLockedException, PasswordNotMatchException, UserNotFoundException and common UserLayerException
        """

        if password is None or not len(password):
            raise UserLayerException("User password is empty")
        
        if new_password is None or not len(new_password):
            raise UserLayerException("New user password is empty")
        
        if not self.__password_validator(new_password):
            raise InvalidUserDataException("New password does not comply the requirements")
        
        user = self.get_user(session_id, user_locale, user_timezone)
        user_name = user.user_name
        if not self.__check_user_credentials(user_name, password):
            raise PasswordNotMatchException("Incorrect password for the user")
                
        try:
            self.__user_data_source.save_user(
                User(
                    user_name,
                    user.roles,
                    user.name,
                    user.locked,
                    user.active,
                    False
                ), 
                self.__password_hash_function(new_password)
            )
            self.close_user_sessions(user_name)
            return self.login(user_name, new_password, user_locale, user_timezone)

        except UserLayerException as e:
            raise e
        except UserDataSourceException as e:
            raise UserLayerException(e) from e
        except Exception as e:
            raise UserLayerException("Unexpected error during password set") from e

    def logout(self, session_id: str) -> None:
        """
        Closes a user session.
        """

        if session_id and session_id in self.__sessions:
            user_session = self.__sessions.pop(session_id)
            user_session_registry = self.__user_session_registry.get(user_session.user.user_name)
            if session_id in user_session_registry:
                user_session_registry.remove(session_id)

    def get_user(self, session_id: str, user_locale: str, user_timezone: str) -> User:
        """
        Returns a user if session is active. 

        Raises: InvalidUserSessionException, UserNotFoundException
        """
        
        if session_id and session_id in self.__sessions:
            user_session = self.__sessions.get(session_id)
            if user_session.is_expired or user_session.locale != user_locale or user_session.timezone != user_timezone:
                raise InvalidUserSessionException(f"User '{user_session.user.user_name}' has an invalid session")
            return user_session.user
        raise UserNotFoundException("No active session found for a visitor with this session")    

    def fetch_user(self, user_name: str):
        """
        Fetches user by its user_name from the data source.

        Raises: UserNotFoundException
        """

        if self.__user_data_source.is_user_exist(user_name):
            try:
                return self.__user_data_source.get_user(user_name)
            except UserDataSourceException as e:
                raise UserLayerException() from e
            
        else:
            raise UserNotFoundException(f"User '{user_name}' is not found")
        
    def fetch_users(self, user_name_part: str, offset: int = 0, limit: int = 10, excluding_user_names: list[str] | str | None = None) -> list[User]:
        try:
            if offset < 0:
                offset = 0
            if limit <= 0:
                limit = 10

            if excluding_user_names:
                excluding_user_names = [excluding_user_names] if isinstance(excluding_user_names, str) else excluding_user_names

            return self.__user_data_source.get_users(user_name_part, offset, limit, excluding_user_names)
            
        except UserDataSourceException as e:
            raise UserLayerException() from e
    
        
    def __validate_user(self, user: User, password: str | None = None, is_registration: bool = True) -> bool:
        if user is None or not isinstance(user, User):
            raise InvalidUserDataException("Uncompatible user object type")
        
        if not isinstance(user.roles, Iterable):
            raise InvalidUserDataException("User roles is not iterable")
        
        roles = self.fetch_roles()

        for role in user.roles:
            if role not in roles:
                raise InvalidUserDataException(f"Role '{role}' is not in the user roles list")

        if is_registration:
            if password is None or not self.__password_validator(password):
                raise InvalidUserDataException("Password does not comply the requirements")

        if user.user_name is None or not self.__user_name_validator(user.user_name):
            raise InvalidUserDataException("Username does not comply the requirements")

    def register_user(self, user: User, password: str) -> User:
        """
        Creates a new user.

        Raises: InvalidUserDataException and common UserLayerException
        """

        self.__validate_user(user, password)
        if self.__user_data_source.is_user_exist(user.user_name):
            raise InvalidUserDataException("Username has already taken")
        
        try:
            return self.__user_data_source.create_user(user, self.__password_hash_function(password))
        except UserDataSourceException as e:
            raise UserLayerException() from e

    def update_user(self, user: User, password: str | None = None) -> User:
        """
        Updates a user. Method is public to be used by administrators.

        Raises: InvalidUserDataException and common UserLayerException
        """

        self.__validate_user(user, password, False)
        if not self.__user_data_source.is_user_exist(user.user_name):
            raise InvalidUserDataException("Username does not exist to update")
        try:
            self.__login_attempts[user.user_name] = 0
            self.close_user_sessions(user.user_name)

            if password is None:
                return self.__user_data_source.update_user(user)
            else:
                return self.__user_data_source.save_user(user, self.__password_hash_function(password))

        except UserDataSourceException as e:
            raise UserLayerException() from e
            
    def update_user_lock(self, user_name: str, lock: bool = True) -> None:
        """
        Locks the user by default. Method is public to be used by administrators.

        Raises: UserLayerException
        """

        if user_name is None or not len(user_name):
            raise UserLayerException("User name is empty")
        
        try:
            self.__user_data_source.update_user_lock(user_name, lock)
            self.close_user_sessions(user_name)
        except UserDataSourceException as e:
            raise UserLayerException() from e

    def clear_expired_sessions(self) -> None:
        """
        Clears all exprired sessions from the service's cache. Method is public to be used by administrators.
        """

        inactive_session_ids = []
        for session_id, user_session in self.__sessions.items():
            if user_session.is_expired:
                inactive_session_ids.append(session_id)
                self.__user_session_registry.get(user_session.user.user_name).remove(session_id)
        
        for inactive_session_id in inactive_session_ids:
            self.__sessions.pop(inactive_session_id)

    def close_user_sessions(self, user_name: str) -> None:
        """
        Closes all user sessions to force them to login again. Method is public to be used by administrators.
        """

        if user_name and user_name in self.__user_session_registry:
            session_ids = self.__user_session_registry.get(user_name)
            self.__user_session_registry[user_name] = []
            for session_id in session_ids:
                self.__sessions.pop(session_id)

    def get_user_sessions(self, user_name: str) -> list[tuple[int, int]]:
        """
        Returns a list of the user active session interval (timestamp tuple, since and till). Only not expired sessions included.
        """

        if user_name and user_name in self.__user_session_registry:
            res = []
            session_ids = self.__user_session_registry.get(user_name)
            for session_id in session_ids:
                session: UserSession = self.__sessions.get(session_id)
                if session and not session.is_expired:
                    res.append((session.expires_at - self.__session_lifespan_seconds, session.expires_at))
            
            return res

        return []
    
    def get_all_user_sessions(self, excluding_user_names: list[str] | str | None) -> dict[User, list[tuple[int, int]]]:
        """
        Returns a list of all users active session interval (timestamp tuple, since and till). Only not expired sessions included.
        """
        
        res = {}
        if excluding_user_names is None:
            excluding_user_names = []
        elif isinstance(excluding_user_names, str):
            excluding_user_names = [excluding_user_names]

        for user_name, session_ids in self.__user_session_registry.items():
            if user_name not in excluding_user_names:
                if session_ids:
                    intervals = []
                    
                    for session_id in session_ids:
                        session: UserSession = self.__sessions.get(session_id)
                        if session and not session.is_expired:
                            intervals.append((session.expires_at - self.__session_lifespan_seconds, session.expires_at))

                    if intervals:
                        try:
                            res[self.__user_data_source.get_user(user_name)] = intervals
                        except UserDataSourceException as e:
                            raise UserLayerException() from e

        return res

    def fetch_roles(self) -> list[str]:
        """
        Fetches all user's roles.
        """

        try:
            return self.__user_data_source.get_roles()
        except UserDataSourceException as e:
            raise UserLayerException() from e

    @property
    def max_login_attempts(self) -> int:
        return self.__max_login_attempts
    
    @property
    def session_lifespan_seconds(self) -> int:
        return self.__session_lifespan_seconds
    
    def validate_user_name(self, user_name: str) -> bool:
        """
        Allows to validate username using the strategy from the constructor.
        """

        return self.__user_name_validator(user_name)
    
    def validate_password(self, password: str) -> bool:
        """
        Allows to validate password using the strategy from the constructor.
        """

        return self.__password_validator(password)

    @staticmethod
    def __make_session_id() -> str:
        return str(uuid4())

