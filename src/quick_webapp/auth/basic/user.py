from collections.abc import Iterable

class User:
    """
    User record class.
    In addition to simple username it has additional flags: active, locked, requires_password_update
    """

    def __init__(self, 
                 user_name: str,
                 roles: list[str],
                 name: str | None = None,
                 locked: bool = False,
                 active: bool = True,
                 requires_password_update: bool = False
    ):
        self.__user_name = user_name
        self.__roles = roles.copy() if roles else []
        self.__name = name
        self.__locked = locked if locked is not None else False
        self.__active = active if active is not None else True
        self.__requires_password_update = requires_password_update if requires_password_update is not None else False

    @property
    def user_name(self):
        """
        Username or login.
        """

        return self.__user_name

    @property
    def name(self) -> str:
        """
        Common person name.
        """

        return self.__name
    
    @property
    def roles(self) -> list[str]:
        """
        List of user roles.
        """

        return self.__roles.copy()
    
    def has_roles(self, roles: str | list[str]) -> bool:
        """
        Checks if roles in user roles. In case of iterable, one role match is enough to claim true (any of element of roles).
        If roles neither string nor iterable - returns false.
        """

        if isinstance(roles, str):
            return roles in self.__roles
        elif isinstance(roles, Iterable):
            for role in roles:
                if role in self.__roles:
                    return True
        return False
    
    @property
    def locked(self):
        return self.__locked
    
    @property
    def active(self):
        return self.__active
    
    @property
    def requires_password_update(self):
        return self.__requires_password_update
    
    def __eq__(self, other):
        if not isinstance(other, User):
            raise ValueError("Comparing object type is not a User")
        return self.__user_name == other.user_name

    def __hash__(self):
        return hash(self.__user_name)
