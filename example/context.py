from typing import Any
from collections.abc import Callable
from pathlib import Path
import os
import signal
import streamlit as st

from quick_webapp.util.shutdown_hook import ShutdownHookHolder
from quick_webapp import bean, session_bean
from quick_webapp.webapp import WebApplication, MenuTree, scan_service_pages, scan_menu_pages, streamlit_main_sctipt_path
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.user_service import UserService
from quick_webapp.security.basic.curent_user_service import CurrentUserService, scan_pages_permissions, filter_only_permitted_menu_pages, filter_only_permitted_service_pages
from quick_webapp.security.basic.data_source import UserDataSource, LocalUserDataSource

@bean
def shutdown_hook_holder() -> ShutdownHookHolder:
    return ShutdownHookHolder("default")

@bean
def menu_handlers() -> dict[str, Callable]:
    return {
        "home": lambda: st.switch_page(home_page()),
        "logout": lambda: current_user_service().logout(),
        "exit": terminate_app
    }

@bean
def webapp() -> WebApplication:
    return WebApplication(
        header_menu={"Exit": "exit"},
        header_menu_command_handlers=menu_handlers(),
        header_buttons_width=150,
        header_buttons_gap=10,
        webapp_dir="webapp"
    )

@bean
def session_id_key() -> str:
    return "session_id"

@bean
def ui_package() -> Path:
    return streamlit_main_sctipt_path().parent / "page"

@bean
def home_page() -> st.Page:
    return st.Page(ui_package() / "home.py")

@bean
def login_page() -> st.Page:
    return st.Page(ui_package() / "login.py")

@bean
def service_pages() -> list[st.Page]:
    return scan_service_pages(ui_package())

@bean
def menu_pages() -> MenuTree:
    return scan_menu_pages(ui_package(), mapper="token_underscore")

@bean
def page_permissions() -> dict[Path, list[str] | None]:
    return scan_pages_permissions(ui_package())

@session_bean
def user_menu_pages() -> MenuTree:
    return filter_only_permitted_menu_pages(menu_pages(), current_user_service(), page_permissions())

@session_bean
def user_service_pages() -> MenuTree:
    return filter_only_permitted_service_pages(service_pages(), current_user_service(), page_permissions())

@bean
def user_data_source() -> UserDataSource:
    return LocalUserDataSource(
        ["user", "admin"],
        "users.db"
    )

@bean
def user_service() -> UserService:
    data_source = user_data_source()

    if not data_source.is_user_exist("user"):
        data_source.create_user(
            User("user", True, True, ["user"]),
            "11111"
        )

        data_source.create_user(
            User("admin", True, True, ["user", "admin"]),
            "11111"
        )
    
    if not data_source.is_user_exist("test_user_1"):
        for i in range(50):
            data_source.create_user(
                User(f"test_user_{i}", True, False, ["user"]),
                "11111"
            )

    return UserService(
        data_source,
        lambda password: password,
        lambda user_input, password: user_input == password,
        lambda user, expires_at: f"{user.user_name}-{expires_at}"
    )

@bean
def current_user_service() -> CurrentUserService:
    return CurrentUserService(
        user_service(),
        login_page=login_page(),
        no_permision_page=home_page(),
        session_id_key=session_id_key()
    )

def terminate_app():
    shutdown_hook_holder().terminate()
    os.kill(os.getpid(), signal.SIGTERM)