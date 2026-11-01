## content

``````
example/
  context.py
  main.py
  page/
    action_table.py
    admin_page.py
    extended_menu_page.py
    home.py
    login.py
    simple_page.py
    user_management/
      all_users.py
      current_users.py
``````

## main.py: entry point
 ``````python
from quick_webapp.webapp import streamlit_page
from context import user_menu_pages, user_service_pages

streamlit_page = streamlit_page(
    user_menu_pages(),
    user_service_pages(),
    "Welcome to example!"
)
streamlit_page.run()
 
``````

## context.py: context and beans
 ``````python
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
from quick_webapp.security.basic.data_source_impl.sqlite import UserDataSource, SQLiteUserDataSource

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
    return SQLiteUserDataSource(
        ["user", "admin"],
        "users.db"
    )

@bean
def user_service() -> UserService:
    data_source = user_data_source()

    if not data_source.is_user_exist("user"):
        data_source.create_user(
            User("user", ["user"]),
            "11111"
        )

        data_source.create_user(
            User("admin", ["user", "admin"]),
            "11111"
        )
    
    if not data_source.is_user_exist("test_user_1"):
        for i in range(50):
            data_source.create_user(
                User(f"test_user_{i}", ["user"]),
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
``````

## page: UI

### action_table.py
 ``````python
import streamlit as st
from quick_webapp import bean, session_bean
from quick_webapp.webapp import menu_page
from quick_webapp.ui.page_context import PageContext
from quick_webapp.ui.action_table import action_table
from context import webapp

class OrderExample:
    def __init__(self, title: str, amount: int, price: float):
        self.__title = title
        self.__amount = amount
        self.__price = price

    @property
    def title(self) -> str:
        return self.__title

    @property
    def amount(self) -> int:
        return self.__amount

    @amount.setter
    def amount(self, value: int):
        self.__amount = value

    @property
    def price(self) -> float:
        return self.__price

def __edit(order: OrderExample, page_context: PageContext):
    order.amount += 1
    page_context.put_notification(f"I am sorta edited order '{order.title}' placing one additional item", "📢")

def __delete(order: OrderExample, page_context: PageContext):
    order.amount -= order.amount
    page_context.put_notification(f"I am sorta deleted order '{order.title}', setting amount to 0", "🚨")

@bean(key="action_table_example_data_mappers")
def __data_mappers() -> dict[str, callable]:
    return {
        "Title": lambda o: st.write(o.title),
        "Amount": lambda o: st.write(f"{o.amount}"),
        "Price": lambda o: st.write(f"${o.price:.2f}"),
        "Total": lambda o: st.write(f"${o.amount * o.price:.2f}")
    }

@session_bean(key="action_table_example_action_mappers")
def __action_mappers() -> dict[str, callable]:
    return {
        "Edit": lambda order: __edit(order, page_context),
        "Delete": lambda order: __delete(order, page_context)
    }

@session_bean(key="action_table_example_page_context")
def __page_context() -> PageContext:
    return PageContext(
        "action_table_example",
        default_context={
            "orders": [
                OrderExample("Apple", 3, 1.25),
                OrderExample("Banana", 5, 0.80),
                OrderExample("Orange", 2, 1.60)
            ]
        }
    )

menu_page("1_UIs", "3_Action table")
with webapp().as_context("UI | Action Table Example"):
    page_context = __page_context()
    st.write("**Orders:**")

    action_table(
            data=__page_context().get_context()["orders"],
            no_data_message="No orders...",
            data_mappers=__data_mappers(),
            action_mappers=__action_mappers(),
            actions_col_label="Actions",
            column_ratio_spec=[6, 2, 2, 1, 1],
            container_width=1000
    )

    page_context.fire_notifications("app")
``````

### admin_page.py
 ``````python
import streamlit as st
from quick_webapp.webapp import menu_page
from context import webapp
from context import current_user_service


menu_page("9_Admin", "1_Welcome, Admin")
current_user_service = current_user_service()
current_user_service.only_permitted("admin")

with webapp().as_context("This is an admin page title"):
    st.write("**You are an admin**")
    if st.button("Exit", type="primary"):
        current_user_service.logout()
``````

### extended_menu_page.py
 ``````python
import streamlit as st
from quick_webapp import bean
from quick_webapp.webapp import menu_page
from context import webapp, ui_package, login_page

@bean(key="go_to_simple_page_switch")
def __go_to_simple_page():
    return lambda: st.switch_page(ui_package() / "simple_page.py")

@bean(key="go_login_switch")
def __go_login():
    return lambda: st.switch_page(login_page())

menu_page("1_UIs", "2_Extended menu")
with webapp().as_context("This is an extended page title", {"To simple page": __go_to_simple_page(), "Go login": __go_login()}):
    st.write("Click on addition button in the menu: **To simple page**")
    st.write("Or click **Go login**")
``````

### home.py
 ``````python
import streamlit as st
from quick_webapp.ui import restart_browser_window
from context import current_user_service
from context import webapp
from quick_webapp.webapp import menu_page

menu_page("0_Home")
current_user_service = current_user_service()
current_user_service.only_permitted()

if st.query_params.get("reload"):
    st.query_params.clear()
    restart_browser_window()

user = current_user_service.get_user()
with webapp().as_context(f"Welcome to Quick WebApp Example, **{user.user_name}**!", page_title_render=st.header):
    pass
``````

### login.py
 ``````python
import streamlit as st
from quick_webapp.ui.security.basic.form import login_form, registration_form, set_password_form
from quick_webapp.ui import read_cookie, get_browser_locate, get_browser_timezone
from quick_webapp.webapp import service_page
from context import webapp, user_service, session_id_key, home_page

service_page()
user_service = user_service()

with webapp().as_context("Login"):
    session_id_key = session_id_key()
    session_id = read_cookie(session_id_key)
    user_locale = get_browser_locate()
    user_timezone = get_browser_timezone()

    if session_id is None or not user_service.is_logged_in(session_id, user_locale, user_timezone):
        registration_clicked = bool(read_cookie("user_wanna_reg", False))
        if registration_clicked:
            registration_form(
                user_service,
                "user",
                True,
                "user_wanna_reg"
            )
        else:
            login_form(
                user_service, 
                session_id_key=session_id_key, 
                registration_key="user_wanna_reg", 
                help_text="This is a help text and lorem ipsum!"
                )
    else:
        if user_service.is_new_password_update_required(session_id):
            set_password_form(
                user_service,
                session_id_key
            )
        else:
            st.switch_page(home_page())
    
``````

### simple_page.py
 ``````python
from typing import Any
import streamlit as st
from quick_webapp import session_bean
from quick_webapp.webapp import menu_page
from context import webapp

@session_bean(key="simple_page_page_context_dict")
def __context() -> dict[str, any]:
    return {}

menu_page("1_UIs", "1_Simple page")

with webapp().as_context(
    page_title="A simple page", 
    page_title_render=lambda t: st.subheader(t),
    java_scripts=["console.log('print to browser!');"]
):
    page_session_obj = __context()
    
    text_input = st.text_area("Type the text:")

    if text_input and len(text_input):
        page_session_obj["last_text"] = text_input

    text_input = page_session_obj.get("last_text")
    if text_input:
        st.write("**You typed:**")
        st.write(text_input)
``````

### user_management/all_users.py
 ``````python
from typing import Any
import streamlit as st
from quick_webapp.webapp import menu_page
from quick_webapp import bean, session_bean
from quick_webapp.ui.action_table import action_table
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.user_service import UserService
from quick_webapp.ui.security.basic.form import edit_user_form
from quick_webapp.ui.page_context import PageContext
from context import webapp, current_user_service, user_service

def __switch_user_lock(user: User, context: dict[str, Any]):
    user_service.update_user_lock(user.user_name, not user.locked)
    context["modified"] = True
    st.rerun()

def __edit_user(user: User, context: dict[str, Any]):
    edit_user_form(user.user_name, user_service)
    context["modified"] = True

@bean(key="user_management_all_users_data_mappers")
def __data_mappers() -> dict[str, callable]:
    return {
        "Username": lambda user: st.write(f"**{user.user_name}**"),
        "Name": lambda user: st.write(user.name if user.name else ':color[Not set]{foreground="#6b6b6b" background="#e3e3e3"}'),
        "Roles": lambda user: st.write(" ".join(f':color[{role}]{{foreground="#f5fffa" background="#464bb4"}}' for role in user.roles)),
        "Locked": lambda user: st.write("🔴" if user.locked else "⚪")
    }

@bean(key="user_management_all_users_action_mappers")
def __action_mappers() -> dict[str, callable]:
    return {
        "🔒": lambda user: __switch_user_lock(user, __page_context().get_context()),
        "📝": lambda user: __edit_user(user, __page_context().get_context())
    }

@session_bean(key="user_management_all_users_page_context")
def __page_context() -> PageContext:
    return PageContext("user_management_all_users")


menu_page("9_User Management", "1_All")
current_user_service = current_user_service()
user_service: UserService = user_service()
current_user_service.only_permitted("admin")

with webapp().as_context("User Management | All", page_title_render=lambda title: st.subheader(title)):
    current_user_name = current_user_service.get_user().user_name
    page_context = __page_context().get_context()
    users_per_page = 10

    with st.container(horizontal=True, vertical_alignment="bottom"):
        q_user_name = st.text_input("User name:", "", width=350)
        if st.button("Search", type="primary") or "q_user_name" not in page_context:
            page_context["q_user_name"] = q_user_name
            page_context["offset"] = 0
            page_context["page"] = user_service.fetch_users(q_user_name, 0, users_per_page, current_user_name)
            page_context["has_next"] = len(page_context["page"]) == users_per_page and len(user_service.fetch_users(q_user_name, users_per_page, 1, current_user_name)) > 0

    if "page" in page_context:
        page = page_context["page"]
        offset = page_context.get("offset", 0)

        if page_context.get("modified"):
            page = user_service.fetch_users(q_user_name, offset, users_per_page, current_user_name)
            page_context["modified"] = False
            page_context["page"] = page

        if page:
            st.write("**Users:**")
            action_table(
                page,
                "No users...",
                __data_mappers(),
                __action_mappers(),
                container_width=800,
                column_ratio_spec=[1, 1.2, 1, 0.4, 0.2, 0.2]
            )

            has_next = page_context.get("has_next")
            has_previous = offset > 0

            if has_next or has_previous:
                clicked = False
                with st.container(horizontal=True):
                    if has_previous:
                        if st.button("<"):
                            clicked = True
                            offset = offset - users_per_page
                            page_context["offset"] = 0 if offset < 0 else offset

                    if has_next:
                        if st.button(">"):
                            clicked = True
                            offset = offset + users_per_page
                            page_context["offset"] = offset
                
                if clicked:
                    page_context["page"] = user_service.fetch_users(q_user_name, offset, users_per_page, current_user_name)
                    page_context["has_next"] = len(page_context["page"]) == users_per_page and len(user_service.fetch_users(q_user_name, offset + users_per_page, 1, current_user_name)) > 0
                    st.rerun()
        else:
            st.write(f"*No users like '{q_user_name}', honey!*")
``````

### user_management/current_users.py
 ``````python
from typing import Any
import streamlit as st
from quick_webapp.webapp import menu_page
from quick_webapp import bean, session_bean
from quick_webapp.ui.page_context import PageContext
from quick_webapp.ui.action_table import action_table
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.user_service import UserService
from quick_webapp.ui.security.basic.form import manage_user_form, edit_user_form
from context import webapp, current_user_service, user_service


def __manage_user(user: User, context: dict[str, Any]):
    context["modified"] = True
    manage_user_form(user.user_name, user_service)

def __edit_user(user: User, context: dict[str, Any]):
    context["modified"] = True
    edit_user_form(user.user_name, user_service)

@bean(key="user_management_current_users_data_mappers")
def __data_mappers() -> dict[str, callable]:
    return {
        "Username": lambda user_session: st.write(f"**{user_session[0].user_name}**"),
        "Name": lambda user_session: st.write(user_session[0].name if user_session[0].name else ':color[Not set]{foreground="#6b6b6b" background="#e3e3e3"}'),
        "Roles": lambda user_session: st.write(" ".join(f':color[{role}]{{foreground="#f5fffa" background="#464bb4"}}' for role in user_session[0].roles)),
        "Sessions": lambda user_session: st.write(len(user_session[1]))
    }

@bean(key="user_management_current_users_action_mappers")
def __action_mappers() -> dict[str, callable]:
    return {
        "🧑‍💼": lambda dict_view: __manage_user(dict_view[0], __page_context().get_context()),
        "📝": lambda dict_view: __edit_user(dict_view[0], __page_context().get_context())
    }

@session_bean(key="user_management_current_users_page_context")
def __page_context() -> PageContext:
    return PageContext("user_management_all_users")

menu_page("9_User Management", "1_Current")
current_user_service = current_user_service()
current_user_service.only_permitted("admin")
user_service: UserService = user_service()

with webapp().as_context("User Management | Current", page_title_render=lambda title: st.subheader(title)):
    current_user_name = current_user_service.get_user().user_name
    current_users = user_service.get_all_user_sessions(current_user_name)

    if current_users:
        st.write("**Active users:**")
        action_table(
            current_users.items(),
            "No current users...",
            __data_mappers(),
            __action_mappers(),
            container_width=800,
            column_ratio_spec=[1, 1.2, 1, 0.4, 0.2, 0.2]
        )
    else:
        st.write("*No active users to manage...*")
``````
