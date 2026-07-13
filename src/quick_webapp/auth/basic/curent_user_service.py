from __future__ import annotations
from typing import Iterable 
import streamlit as st
from pathlib import Path
from quick_webapp.auth.basic.user import User
from quick_webapp.auth.basic.user_service import UserService, InvalidUserSessionException, UserNotFoundException
import quick_webapp.util.ui as ui
from quick_webapp.util.reflection import scan_params

def scan_pages_permissions(
    ui_package_root: str | Path,
    *ui_package_path: str
) -> dict[Path, list[str] | None]:
    """
    Scans and returns a dict with paths to .py files and its roles, used with method only_permitted. Useful to build UI based on user roles.
    If file call only_permitted(list) then result dictionary will have those as is, ergo path: args
    If file call only_permitted(str) then result dictionary will have the args as a list with one element, ergo path: [args]
    If file call only_permitted() then result dictionary will have an empty list, ergo path: []
    If file has no call of only_permitted then result dictionary will have None, ergo path: None
    """

    permission_items: dict[Path, list[str] | None] = {}

    only_permitted_calls = scan_params(
        "only_permitted",
        ui_package_root,
        *ui_package_path
    )

    for file, calls in only_permitted_calls.items():
        if not calls:
            permission_items[file] = None
            continue
        
        roles = []
        permission_items[file] = roles

        first = calls[0]
        kwarg = first["kwargs"].get("with_roles")

        if kwarg:
            if isinstance(kwarg, str):
                roles.append(kwarg)
            elif isinstance(kwarg, Iterable):
                roles.extend(kwarg)
        
        else:
            roles.extend(first["args"])

    return permission_items


def filter_current_user_menu_pages(menu_pages: dict[str, dict[str, Path]], current_user_service: CurrentUserService, permission_map: dict[Path, list[str] | None]) -> dict[str, dict[str, Path]]:
    """
    Filters target's current user persissions.
    For not logged in users only files that does not have only_permitted(...) or not in the permission_map calls be included.
    For logged in also files that have both noargs only_permitted() and only_permitted(roles) with user-roles be included.

    Otherwise, it filters out the Paths that explicetly protected with only_permitted(...)

    - not in permission_map - anyone
    - permission_map[e] is None - anyone
    - permission_map[e] is [] - logged in
    - permission_map[e] is [r1, r2, ...] - logged in that has any of the roles
    """

    try:
        user = current_user_service.get_user()
        res = {}
        for menu_label, menu in menu_pages.items():
            current_user_menu = {}

            for sublabel, path in menu.items():
                roles = permission_map.get(path)
                if not roles or user.has_roles(roles):
                    current_user_menu[sublabel] = path
            
            if current_user_menu:
                res[menu_label] = current_user_menu

        return res

    except (InvalidUserSessionException, UserNotFoundException):
        public_pages = {}

        for menu_label, menu in menu_pages.items():
            current_user_menu = {}

            for sublabel, path in menu.items():
                roles = permission_map.get(path)
                if roles is None:
                    current_user_menu[sublabel] = path
            
            if current_user_menu:
                public_pages[menu_label] = current_user_menu

        return public_pages
    
    except:
        raise


class CurrentUserService:
    """
    Service layer class to maintain current user authentication. 
    Acts like a readonly + redirector facade for UserService to encapsulate default behaviour in logged (current) user scope.
    The goal is to reduce the pages code in part of determining what is allowed for the current user.
    Caller may choose to use imperative way with is_logged_in() + is_new_password_update_required() + is_allowed(roles) to check and process current user loging state or simply declarativelly use only_permitted() method.
    To login, update and maintain user/users use UserService.
    """

    def __init__(self,
                 user_service: UserService,
                 login_page: str | Path,
                 no_permision_page: str | Path,
                 no_permision_query_key: str = "reload",
                 no_permision_query_value: str = True,
                 session_id_key = "session_id"
        ):
        self.__user_service = user_service
        self.__login_page = login_page
        self.__no_permision_page = no_permision_page
        self.__no_permision_key = no_permision_query_key
        self.__no_permision_value = no_permision_query_value
        self.__session_id_key = session_id_key
    
    def __fetch_session_values(self) -> tuple[str, str, str]:
        session_id = ui.read_cookie(self.__session_id_key)
        if session_id is not None:
            return (
                session_id,
                ui.get_browser_locate(),
                ui.get_browser_timezone()
            )
        raise InvalidUserSessionException(f"Current user has an invalid session")

    def get_user(self) -> User:
        """
        Fetcher current user.

        Raises: all from UserService.get_user()
        """

        return self.__user_service.get_user(*self.__fetch_session_values())
    
    def is_logged_in(self) -> bool:
        """
        Checks if current user is logged in and it session is valid.
        """

        try:
            return self.__user_service.is_logged_in(*self.__fetch_session_values())
        except:
            return False
    
    def is_new_password_update_required(self) -> bool:
        """
        Checks if corrent user must update the password.
        """

        try:
            return self.__user_service.is_new_password_update_required(ui.read_cookie(self.__session_id_key))
        except:
            return False

    def is_allowed(self, with_roles: list[str] | str) -> bool:
        """
        Checks if current user has the roles in their roles.
        If with_role is null/empty then returns false (real value must be providen or do not call this method)
        """
        try:
            return self.__user_service.is_allowed(ui.read_cookie(self.__session_id_key), with_roles)
        except:
            return False
    
    def only_permitted(self, with_roles: list[str] | str = None):
        """
        Check if current user is logged in, doesn't need to set the password or has appropriate roles.
        Also, it is a marker method for automagic that scans the allowed .py files for a specific user role (see get_permissions method)
        In login/password/exception cases will be redirected (with Streamlit mechanism) to the login_page, specified in constructor. 
        In case where user has no role will be redirected (with Streamlit mechanism) to the no_permision_page with query params no_permision_key=no_permision_value, specified in constructor. 
        Method differs from is_allowed in case with absence of with_roles - if the value is null then no role check is perform.
        """
        
        try:
            session_id, locale, timezone = self.__fetch_session_values()
            if (
                self.__user_service.is_logged_in(session_id, locale, timezone) and
                not self.__user_service.is_new_password_update_required(session_id)
            ):
                if with_roles is not None and not self.__user_service.is_allowed(session_id, with_roles):
                    st.switch_page(self.__no_permision_page, query_params={self.__no_permision_key: self.__no_permision_value})
            else:
                st.switch_page(self.__login_page)
        except Exception as e:
            st.switch_page(self.__login_page)

            
    def logout(self):
        """
        Invalidates the current user session and switch to login page.
        Method is to logout within code or a custom user button.
        """

        try:
            self.__user_service.logout(ui.read_cookie(self.__session_id_key))
        except:
            pass
        finally:
            st.switch_page(self.__login_page)

    

    

