from typing import Any
from collections.abc import Callable, Iterable
from uuid import uuid4
import time
import threading
import json
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.data_source import UserDataSource, UserDataSourceException


class UserLayerException(Exception):
    """Common user layer related exception."""
    pass

class UserNotFoundException(UserLayerException):
    """Exception-indicator of user's absence."""
    pass

class PasswordNotMatchException(UserLayerException):
    """Exception-indicator of user's password checking fail."""
    pass

class PasswordToBeSetException(UserLayerException):
    """Exception-indicator that user must set the password to work with the application."""
    pass

class UserNotActiveException(UserLayerException):
    """Exception-indicator of user's inactivity."""
    pass

class UserLockedException(UserLayerException):
    """Exception-indicator of user being locked."""
    pass

class InvalidUserDataException(UserLayerException):
    """Exception for user record validation errors."""
    pass

class InvalidUserSessionException(UserLayerException):
    """Exception-indicator of user's session is invalid."""
    pass

class UserNotAllowedException(UserLayerException):
    """Exception-indicator of user is not allowed to use a service/authentication method."""
    pass

class Session:
    """
    Common session class.
    """

    def __init__(self,
                 expires_at: int,
                 user: User
    ):
        self.__expires_at: int = expires_at
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
    def user(self) -> User:
        """
        User record of this session.
        """

        return self.__user
    
class UserSession(Session):
    """
    User session record class.
    """

    def __init__(self,
                 expires_at: int,
                 locale: str,
                 timezone: str, 
                 user_agent: str | None,
                 ip_address: str | None,
                 user: User
    ):
        super().__init__(expires_at, user)
        self.__locale = locale
        self.__timezone = timezone
        self.__user_agent = user_agent
        self.__ip_address = ip_address
    
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
    def user_agent(self) -> str | None:
        """
        User agent (browser) string.
        """
                
        return self.__user_agent

    @property
    def ip_address(self) -> str:
        """
        User IP address string.
        """
                
        return self.__ip_address
    
    
    def is_valid(self, locale: str, timezone: str, user_agent: str | None, ip_address: str | None) -> bool:
        """
        Check is session is valid now.
        """

        return not self.is_expired and self.__locale == locale and self.__timezone == timezone and user_agent == self.__user_agent and ip_address == self.__ip_address

class SessionsInfo:
    """
    Session info record class.
    """
        
    def __init__(self, user: User, user_sessions_lifespans: Iterable[Iterable[int, int]], token_sessions_lifespans: Iterable[Iterable[int, int]]):
        self.__user = user
        self.__user_sessions_lifespans = tuple(user_sessions_lifespans)
        self.__token_sessions_lifespans = tuple(token_sessions_lifespans)

    @property
    def user(self) -> User:
        """
        User record of this session info.
        """
        return self.__user

    @property
    def user_sessions_lifespans(self) -> tuple[Iterable[int, int]]:
        """
        A list of users sessions lifespans in for on since - till POSIXes.
        """

        return self.__user_sessions_lifespans

    @property
    def user_sessions_count(self) -> int:
        """
        A count of user sessions.
        """

        return len(self.__user_sessions_lifespans)

    @property
    def token_sessions_lifespans(self) -> tuple[Iterable[int, int]]:
        """
        A list of token sessions lifespans in for on since - till POSIXes.
        """

        return self.__token_sessions_lifespans

    @property
    def token_sessions_count(self) -> int:
        """
        A count of token sessions.
        """
        return len(self.__token_sessions_lifespans)

class UserService:
    """
    Service layer class to maintain user-password based authorization.
    The service must be initialized within constructor, where user provides data source, password hash gen/check function, token generator, validators and constants.
    Methods may return string with session ID (so UI related flow store it in cache), a User object (to display/edit the user), user token (so it can be used in APIs) and bool checks.

    """

    def __init__(self,
        user_data_source: UserDataSource,
        password_hash_function: Callable[[str], str],
        password_hash_check_function: Callable[[str, str], bool],
        token_generator: Callable[[User, int], str],
        details_cipher_function: Callable[[str], str] = lambda plain_user_details: plain_user_details,
        details_decipher_function: Callable[[str], str] = lambda ciphered_user_details: ciphered_user_details,
        user_name_validator: Callable[[str], bool] = lambda user_name: True,
        password_validator: Callable[[str], bool] = lambda passsword: True,
        token_validator: Callable[[str], bool] = lambda token: True,
        max_login_attempts = 3,
        session_lifespan_seconds = 3600
    ):
        """
        A UserService contructor

        - user_data_source: is a UserDataSource where User records are stored
        - password_hash_function: a function that hashes user input (password, always is passed not None and not blank) into stored hash
        - password_hash_check_function: a function that checks if the user input (password, 1st argument, always is passed not None and not blank) complient to the hash (2nd argument)
        - user_name_validator: a function that validates username (always is passed not None and not blank) by external rule
        - password_validator: a function that validates password (always is passed not None and not blank) by external rule
        - token_generator: a function that derives a token from a User (1st argument) and expiration date (2nd argument, POSIX int)
        - token_prevalidator: a function that validates token (always is passed not None and not empty but possibly blank though) by external rule
        - max_login_attempts: a maximum login attempts count, shared with both login and token based auth so user will be blocked after this limit exceeds
        - session_lifespan_seconds: a session lifespan (now() plus this value), shared with both login and token based auth so the session will be invalidated after this time exceeds
        """

        self.__user_data_source: UserDataSource = user_data_source
        self.__details_cipher_function = details_cipher_function
        self.__details_decipher_function = details_decipher_function
        self.__password_hash_function: Callable[[str], str] = password_hash_function
        self.__password_hash_check_function : Callable[[str, str], bool] = password_hash_check_function

        self.__user_name_validator: Callable[[str], bool] = user_name_validator
        self.__password_validator: Callable[[str], bool] = password_validator
        self.__user_session_registry: dict[str, list[str]] = {}
        self.__user_sessions: dict[str, UserSession] = {}
        self.__user_sessions_lock = threading.Lock()

        self.__token_generator = token_generator
        self.__token_validator = token_validator
        self.__token_session_registry: dict[str, list[str]] = {}
        self.__token_sessions: dict[str, Session] = {}
        self.__token_sessions_lock = threading.Lock()

        self.__max_login_attempts: int = max_login_attempts
        self.__login_attempts: dict[str, int] = {}
        self.__login_attempts_lock = threading.Lock()

        self.__session_lifespan_seconds = session_lifespan_seconds

    def __check_user_credentials(self, user_name: str, password: str) -> None:
            used_login_attempts = self.__login_attempts.get(user_name, 0)
            if used_login_attempts >= self.__max_login_attempts:
                raise UserLockedException(f"User '{user_name}' has exceeded {self.__max_login_attempts} login attempts")
    
            if not self.__password_hash_check_function(password, self.__user_data_source.get_user_password(user_name)):
                used_login_attempts += 1

                with self.__login_attempts_lock:
                    self.__login_attempts[user_name] = used_login_attempts

                if used_login_attempts >= self.__max_login_attempts:
                    self.update_user_lock(user_name)
                    raise UserLockedException(f"User '{user_name}' has been locked")
                raise PasswordNotMatchException(f"Incorrect password for user '{user_name}'")
            
    def __prepare_user_name_input(self, user_name: str) -> str:
        if user_name is None or not (user_name := user_name.strip()):
            raise InvalidUserDataException("Username is empty")

        if not self.__user_name_validator(user_name):
            raise InvalidUserDataException("Username does not comply the requirements")

        return user_name
    
    def __prepare_password_input(self, password: str) -> str:
        if password is None or not (password := password.strip()):
            raise InvalidUserDataException("Password is empty")

        if not self.__password_validator(password):
            raise InvalidUserDataException("Password does not comply the requirements")

        return password

    def __prepare_user(self, user: User) -> User:
        if user is None:
            raise InvalidUserDataException("User object is empty")
        
        if not isinstance(user, User):
            raise InvalidUserDataException("Uncompatible user object type")

        user_name = self.__prepare_user_name_input(user.user_name)
        roles = self.fetch_roles()

        for role in user.roles:
            if role not in roles:
                raise InvalidUserDataException("Unknown user role, not from the domain user roles list")

        return User(user_name, user.is_ui_user, user.is_service_user, user.roles, user.name, user.locked, user.active, user.requires_password_update)

    def fetch_roles(self) -> list[str]:
        """
        Fetches all user's roles.
        """

        try:
            return self.__user_data_source.get_roles()
        except UserDataSourceException as e:
            raise UserLayerException() from e

    def login(self, user_name: str, password: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> str:
        """
        Logins the user and set the session. Returns a session ID if user allowed to login.
        If user exceeds max_login_attempts, user will be locked.

        Raises: UserLockedException, PasswordNotMatchException, UserNotFoundException and common UserLayerException
        """
            
        user_name = self.__prepare_user_name_input(user_name)
        password = self.__prepare_password_input(password)
            
        try:
            if not self.__user_data_source.is_user_exist(user_name):
                raise UserNotFoundException(f"User '{user_name}' is not found")
                
            self.__check_user_credentials(user_name, password)
            user = self.__user_data_source.get_user(user_name)

            if not user.is_ui_user:
                raise UserNotAllowedException(f"User '{user_name}' is not allowed to login")
            if not user.active:
                raise UserNotActiveException(f"User '{user_name}' is not active")
            if user.locked:
                raise UserLockedException(f"User '{user_name}' is locked")
                
            session_id = str(uuid4())
            user_session = UserSession(time.time() + self.__session_lifespan_seconds, user_locale, user_timezone, user_agent, ip_address, user)

            with self.__user_sessions_lock:
                self.__user_sessions[session_id] = user_session
                if user_name not in self.__user_session_registry:
                    sessions = []
                    sessions.append(session_id)
                    self.__user_session_registry[user_name] = sessions
                else:
                    self.__user_session_registry[user_name].append(session_id)

            with self.__login_attempts_lock:
                self.__login_attempts[user_name] = 0

            return session_id

        except UserLayerException as e:
            raise e
        except UserDataSourceException as e:
            raise UserLayerException() from e
        except Exception as e:
            raise UserLayerException("Unexpected error during login") from e

    def is_logged_in(self, session_id: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> bool:
        """
        Checks if the user is logged in and it session is valid.
        """

        if session_id and session_id in self.__user_sessions:
            user_session = self.__user_sessions.get(session_id)
            if user_session.is_valid(user_locale, user_timezone, user_agent, ip_address):
                user = user_session.user
                return user.active and not user.locked
        return False
    
    def is_new_password_update_required(self, session_id: str) -> bool:
        """
        Checks if the session user must update the password. Only session_id is required.
        """

        if session_id and session_id in self.__user_sessions:
            user = self.__user_sessions.get(session_id).user
            return user.requires_password_update
        return False
    
    def is_allowed(self, session_id: str, with_roles: str | list[str] | None = None) -> bool:
        """
        Checks if the user has the role in their roles. Only session_id is required.
        
        If with_role is null/empty or element of the with_role contains not string, returns False.
        """

        if with_roles and session_id:
            user_session = self.__user_sessions.get(session_id)
            if user_session:
                return user_session.user.has_roles(with_roles)

        return False

    def set_password(self, session_id: str, password: str, new_password: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> str:
        """
        Sets tne current user password, clears all sessions and relogins, returning a new session id.
        Password policy as the same as for login - user will be locked if the current password does not match max_login_attempts.
        User property requires_password_update after successfull password set will be False.
        User state policy also the same - user will able to set password but for unlock/making active, use update_user()

        Returns: a session ID string

        Raises: InvalidUserSessionException, UserLockedException, PasswordNotMatchException, UserNotFoundException and common UserLayerException
        """

        password = self.__prepare_password_input(password)
        new_password = self.__prepare_password_input(new_password)
        
        user = self.get_user(session_id, user_locale, user_timezone, user_agent, ip_address)
        user_name = user.user_name
        self.__check_user_credentials(user_name, password)
                
        try:
            self.__user_data_source.save_user(
                User(
                    user_name,
                    user.is_ui_user,
                    user.is_service_user,
                    user.roles,
                    user.name,
                    user.locked,
                    user.active,
                    False
                ), 
                self.__password_hash_function(new_password)
            )
            self.close_all_sessions(user_name)
            return self.login(user_name, new_password, user_locale, user_timezone, user_agent, ip_address)

        except UserLayerException as e:
            raise e
        except UserDataSourceException as e:
            raise UserLayerException() from e
        except Exception as e:
            raise UserLayerException("Unexpected error during password set") from e

    def logout(self, session_id: str) -> None:
        """
        Closes a user session.
        """

        if session_id:
            with self.__user_sessions_lock:
                if session_id in self.__user_sessions:
                    user_session = self.__user_sessions.pop(session_id)
                    user_session_registry = self.__user_session_registry.get(user_session.user.user_name)
                    if session_id in user_session_registry:
                        user_session_registry.remove(session_id)

    def get_user(self, session_id: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> User:
        """
        Returns a user if session is active. 

        Raises: InvalidUserSessionException, UserNotFoundException
        """
        
        if session_id:
            user_session = self.__user_sessions.get(session_id)
            if user_session:
                if not user_session.is_valid(user_locale, user_timezone, user_agent, ip_address):
                    raise InvalidUserSessionException("User has an invalid session")
                return user_session.user
            
        raise UserNotFoundException("No active session found for a visitor with this session")    

    def __fetch_user_details(self, user_name: str) -> dict[str, Any]:
        try:
            details_str = self.__details_decipher_function(self.__user_data_source.get_user_details(user_name))
            return json.loads(details_str)
            
        except UserDataSourceException as e:
            raise UserLayerException() from e
        except json.JSONDecodeError as e:
            raise UserLayerException("Unable to deserialize the user details from deciphered text") from e
        except Exception as e:
            raise UserLayerException("Unexpected error during user details deserialization") from e

    def __make_user_details_str(self, details: dict[str, Any] | None) -> str:
        try:
            return self.__details_cipher_function(json.dumps(details if details else {}))
        except json.JSONDecodeError as e:
            raise UserLayerException("Unable to deserialize the user details from deciphered text") from e
        except Exception as e:
            raise UserLayerException("Unexpected error during user details serialization") from e

    def get_user_details(self, session_id: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> dict[str, Any]:
        """
        Returns a user details if session is active. 

        Raises: InvalidUserSessionException, UserNotFoundException
        """
        
        if session_id:
            user_session = self.__user_sessions.get(session_id)
            if user_session:
                if not user_session.is_valid(user_locale, user_timezone, user_agent, ip_address):
                    raise InvalidUserSessionException("User has an invalid session")

                return self.__fetch_user_details(user_session.user.user_name)
            
        raise UserNotFoundException("No active session found for a visitor with this session")   

    def fetch_user(self, user_name: str) -> User:
        """
        Fetches user by its user_name from the data source. It is a service method, not user-specific, not user_name

        Raises: UserNotFoundException (even in cases where user_name itself is empty or not a string)
        """

        if user_name and isinstance(user_name, str) and self.__user_data_source.is_user_exist(user_name):
            try:
                return self.__user_data_source.get_user(user_name)
            except UserDataSourceException as e:
                raise UserLayerException() from e
            
        raise UserNotFoundException("User is not found")

    def fetch_user_details(self, user_name: str) -> dict[str, Any]:
        """
        Fetches user details by its user_name from the data source. It is a service method, not user-specific, not user_name

        Raises: UserNotFoundException (even in cases where user_name itself is empty or not a string)
        """

        if user_name and isinstance(user_name, str) and self.__user_data_source.is_user_exist(user_name):
            return self.__fetch_user_details(user_name)
            
        raise UserNotFoundException("User is not found")
        
    def fetch_users(
        self, 
        user_name_part: str, 
        offset: int = 0, 
        limit: int = 10, 
        excluding_user_names: list[str] | str | None = None
    ) -> list[User]:
        """
        Fetches users by a user_name part in paging way.
        """

        try:
            if offset < 0:
                offset = 0
            if limit <= 0:
                limit = 10

            if excluding_user_names:
                excluding_user_names = [excluding_user_names] if isinstance(excluding_user_names, str) else excluding_user_names

            if not user_name_part:
                user_name_part = ""

            return self.__user_data_source.get_users(user_name_part, offset, limit, excluding_user_names)
            
        except UserDataSourceException as e:
            raise UserLayerException() from e

    def register_user(self, user: User, password: str, details: dict[str, Any] | None = None) -> User:
        """
        Creates a new user.

        Raises: InvalidUserDataException and common UserLayerException
        """

        password = self.__prepare_password_input(password)
        user = self.__prepare_user(user)

        if self.__user_data_source.is_user_exist(user.user_name):
            raise InvalidUserDataException("Username has already taken")
        
        try:
            return self.__user_data_source.create_user(user, self.__password_hash_function(password), self.__make_user_details_str(details))
        except UserDataSourceException as e:
            raise UserLayerException() from e

    def update_user(self, user: User, password: str | None = None, details: dict[str, Any] | None = None) -> User:
        """
        Updates a user. Method is public to be used by administrators.
        """

        user = self.__prepare_user(user)
        
        if not self.__user_data_source.is_user_exist(user.user_name):
            raise InvalidUserDataException("Username does not exist to update")
        try:
            details_str = None if details is None else self.__make_user_details_str(details)

            if password is None:
                return self.__user_data_source.update_user(user, details_str)
            else:
                return self.__user_data_source.save_user(user, self.__password_hash_function(self.__prepare_password_input(password)), details_str)

        except UserDataSourceException as e:
            raise UserLayerException() from e

        finally:
            with self.__login_attempts_lock:
                self.__login_attempts[user.user_name] = 0
            
            self.close_all_sessions(user.user_name)
            
    def update_user_lock(self, user_name: str, lock: bool = True) -> None:
        """
        Locks the user by default. Method is public to be used by administrators.

        Raises: UserLayerException
        """

        if user_name is None or not len(user_name):
            raise UserLayerException("User name is empty")
        
        try:
            self.__user_data_source.update_user_lock(user_name, lock)
            self.close_all_sessions(user_name)
        except UserDataSourceException as e:
            raise UserLayerException() from e

    def get_token(self, user_name: str, password: str) -> tuple[str, int]:
        """
        Authenticate user and generate an API token.

        Returns the token and expiration timestamp (in seconds POSIX).
        """

        self.__check_user_credentials(user_name, password)
        user = self.fetch_user(user_name)

        if not user.is_service_user:
            raise UserNotAllowedException(f"User '{user_name}' is not allowed to generate token")
        if not user.active:
            raise UserNotActiveException(f"User '{user_name}' is not active")
        if user.locked:
            raise UserLockedException(f"User '{user_name}' is locked")

        with self.__token_sessions_lock:
            expires_at = time.time() + self.__session_lifespan_seconds
            token = self.__token_generator(user, expires_at)

            self.__token_sessions[token] = Session(expires_at, user)
            if user_name not in self.__token_session_registry:
                self.__token_session_registry[user_name] = [token]
            else:
                self.__token_session_registry[user_name].append(token)

        return (token, expires_at)

    def is_token_valid(self, token: str) -> bool:
        """
        Validate API token and return associated username.
        Returns False if token is invalid (not expired and token prevalidator returned True) or the user is locked/not active.
        """

        if token and self.__token_validator(token):
            token_session = self.__token_sessions.get(token)

            if token_session:
                user = token_session.user
                return not token_session.is_expired() and user.active and not user.locked

        return False

    def is_token_allowed(self, token: str, with_roles: str | list[str] | None = None) -> bool:
        """
        Checks if the user has any role of the with-roles in their roles. Only session_id is required.
        
        If with_role and token are null/empty then returns False, otherwise behaves like is_token_valid() just with roles checking.
        """

        if token and with_roles and self.__token_validator(token):
            token_session = self.__token_sessions.get(token)
            if token_session:
                user = token_session.user
                return not token_session.is_expired() and user.active and not user.locked and user.has_roles(with_roles)
        
        return False

    def get_user_sessions_info(self, user_name: str) -> SessionsInfo | None:
        """
        Returns a SessionsInfo of the user and token active session intervals (timestamp tuple, since and till). Only not expired sessions included.
        """

        if user_name:
            user = None
            user_sessions_lifespans = []
            token_sessions_lifespans = []

            with self.__user_sessions_lock:
                if user_name in self.__user_session_registry:
                    session_ids = self.__user_session_registry.get(user_name)
                    for session_id in session_ids:
                        session: UserSession = self.__user_sessions.get(session_id)
                        if not session.is_expired:
                            user_sessions_lifespans.append((session.expires_at - self.__session_lifespan_seconds, session.expires_at))
                            user = session.user

            with self.__token_sessions_lock:
                if user_name in self.__token_session_registry:
                    tokens = self.__token_session_registry.get(user_name)
                    for token in tokens:
                        token_session: Session = self.__token_sessions.get(token)
                        if not token_session.is_expired:
                            token_sessions_lifespans.append((token_session.expires_at - self.__session_lifespan_seconds, token_session.expires_at))
                            user = token_session.user

            if not user:
                raise UserLayerException("User does not have active sessions")

            return SessionsInfo(user, user_sessions_lifespans, token_sessions_lifespans)
        
        raise UserLayerException("Username is empty")

    def get_all_sessions_info(
        self, 
        user_name_part: str, 
        offset: int = 0, 
        limit: int = 10, 
        excluding_user_names: list[str] | str | None = None
    ) -> list[SessionsInfo]:
        """
        Returns a list of SessionsInfo of the user and token active session intervals (timestamp tuple, since and till). Only not expired sessions included.
        """

        user_names = []

        with self.__user_sessions_lock:
            user_names.extend(self.__user_session_registry.keys())

        with self.__token_sessions_lock:
            user_names.extend(self.__token_session_registry.keys())

        if offset < 0:
            offset = 0
        if limit <= 0:
            limit = 10

        if excluding_user_names is None:
            excluding_user_names = []
        elif isinstance(excluding_user_names, str):
            excluding_user_names = [excluding_user_names]

        if user_name_part:
            user_names = list(filter(lambda user_name: user_name not in excluding_user_names and user_name_part in user_name, user_names))
        else:
            user_names = list(filter(lambda user_name: user_name not in excluding_user_names, user_names))
        
        res = []
        for user_name in user_names[offset:limit]:
            try:
                res.append(self.get_user_sessions_info(user_name))
            except:
                pass

        return res

    def clear_all_expired_sessions(self) -> None:
        """
        Clears all exprired sessions (both user and token) from the service's cache. Method is public to be used by administrators.
        """

        with self.__user_sessions_lock:
            inactive_session_ids = []
            for session_id, user_session in self.__user_sessions.items():
                if user_session.is_expired:
                    inactive_session_ids.append(session_id)
                    self.__user_session_registry.get(user_session.user.user_name).remove(session_id)
            
            for inactive_session_id in inactive_session_ids:
                self.__user_sessions.pop(inactive_session_id)

        with self.__token_sessions_lock:
            inactive_tokens = []
            for token, token_session in self.__token_sessions.items():
                if token_session.is_expired():
                    inactive_tokens.append(token)
                    self.__token_session_registry.get(token_session.user.user_name).remove(token)

            for inactive_token in inactive_tokens:
                self.__token_sessions.pop(inactive_token)

    def close_all_sessions(self, user_name: str) -> None:
        """
        Closes all sessions (both user and token) to force them to login/get token again. Method is public to be used by administrators.
        """

        if user_name:
            with self.__user_sessions_lock:
                if user_name in self.__user_session_registry:
                    session_ids = self.__user_session_registry.get(user_name)
                    self.__user_session_registry[user_name] = []
                    for session_id in session_ids:
                        self.__user_sessions.pop(session_id)
            
            with self.__token_sessions_lock:
                if user_name in self.__token_session_registry:
                    tokens = self.__token_session_registry.get(user_name)
                    self.__token_session_registry[user_name] = []
                    for token in tokens:
                        self.__token_sessions.pop(token)

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

        return user_name and self.__user_name_validator(user_name)
    
    def validate_password(self, password: str) -> bool:
        """
        Allows to validate password using the strategy from the constructor.
        """

        return password and password.strip() and self.__password_validator(password.strip())
