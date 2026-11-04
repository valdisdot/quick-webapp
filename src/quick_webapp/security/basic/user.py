from collections.abc import Sequence

class User:
    """
    User record class.
    In addition to simple username it has additional flags: active, locked, requires_password_update
    Serves DTO fucntion (when passed into the service) and record function (when used inside the service).
    """

    def __init__(self, 
                 user_name: str,
                 is_ui_user,
                 is_service_user,
                 roles: list[str],
                 name: str | None = None,
                 locked: bool = False,
                 active: bool = True,
                 requires_password_update: bool = False
    ):
        self.__user_name = user_name.strip() if user_name is not None and isinstance(user_name, str) else None
        self.__is_ui_user = bool(is_ui_user)
        self.__is_service_user = bool(is_service_user)
        self.__roles = roles.copy() if roles and isinstance(roles, Sequence) else []
        self.__name = str(name) if name is not None and isinstance(name, str) else None
        self.__locked = bool(locked)
        self.__active = bool(active)
        self.__requires_password_update = bool(requires_password_update)

    @property
    def user_name(self) -> str:
        """
        Username or login.
        None if contructor user_name arg was None or not string.
        Retuns stripped version of contructor user_name arg.
        """

        return self.__user_name

    @property
    def is_ui_user(self) -> bool:
        """
        Is user allowed to login flag.
        """

        return self.__is_ui_user

    @property
    def is_service_user(self) -> bool:
        """
        Is user allowed to use services (APIs) flag.
        """

        return self.__is_service_user

    @property
    def name(self) -> str:
        """
        Common person name.
        None if contructor name args was None or not string.
        """

        return self.__name
    
    @property
    def roles(self) -> list[str]:
        """
        List of user roles (copy of)
        """

        return self.__roles.copy()
    
    def has_roles(self, roles: str | Sequence[str]) -> bool:
        """
        Checks if any of roles is in user roles. In case of a sequence, one role match is enough to claim true (any of element of roles).
        If roles is empty, or neither string nor sequence - returns false.
        """

        if roles:
            if isinstance(roles, str):
                return roles in self.__roles
            elif isinstance(roles, Sequence):
                for role in roles:
                    if role in self.__roles:
                        return True
        return False
    
    @property
    def locked(self) -> bool:
        """
        Is user locked flag.
        """

        return self.__locked
    
    @property
    def active(self) -> bool:
        """
        Is user active flag.
        """

        return self.__active
    
    @property
    def requires_password_update(self) -> bool:
        """
        Is user must set a new password flag.
        """

        return self.__requires_password_update
    
    def __eq__(self, other):
        if not isinstance(other, User):
            raise ValueError("Comparing object type is not a User")
        return self.__user_name == other.user_name

    def __hash__(self):
        return hash(self.__user_name)
