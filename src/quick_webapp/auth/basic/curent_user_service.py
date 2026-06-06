import streamlit as st
from quick_webapp.auth.basic.user import User
from quick_webapp.auth.basic.user_service import UserService, InvalidUserSessionException
import quick_webapp.util.ui as ui

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
                 login_page: str,
                 no_permision_page: str,
                 session_id_key = "session_id",
        ):
        self.__user_service = user_service
        self.__login_page = login_page
        self.__no_permision_page = no_permision_page
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

    def is_allowed(self, with_role: list[str] | str) -> bool:
        """
        Checks if current user has the roles in their roles.
        If with_role is null/empty then returns false (real value must be providen or do not call this method)
        """
        try:
            return self.__user_service.is_allowed(ui.read_cookie(self.__session_id_key), with_role)
        except:
            return False
    
    def only_permitted(self, with_roles: list[str] | str = None):
        """
        Check if current user is logged in, doesn't need to set the password or has appropriate roles.
        In login/password cases will be redirected (with Streamlit mechanism) to login page, specified in constructor. 
        In case where user has no role will be redirected (with Streamlit mechanism) to appropriabe page, specified in constructor. 
        Method is differs from is_allowed in case with absence of with_roles - if the value is null then no role check is perform.
        """
        
        try:
            session_id, locale, timezone = self.__fetch_session_values()
            if (
                self.__user_service.is_logged_in(session_id, locale, timezone) and
                not self.__user_service.is_new_password_update_required(session_id)
            ):
                if with_roles is not None and not self.__user_service.is_allowed(session_id, with_roles):
                    st.switch_page(self.__no_permision_page)
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

    

    

