## content

``````
example/
  config.py
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
from quick_webapp.webapp import WebApplication, streamlit_page
from config import webapp, user_menu_pages, service_pages

web_app: WebApplication = webapp()
streamlit_page = streamlit_page(
    user_menu_pages(),
    service_pages(),
    "Welcome to example!"
)
streamlit_page.run()
 
``````

## config.py: context and beans
 ``````python
from typing import Any
from collections.abc import Callable
from pathlib import Path
import os
import signal
import streamlit as st

from quick_webapp.service import ensure_shutdown_hook_holder
from quick_webapp import bean, session_bean
from quick_webapp.webapp import WebApplication, scan_service_pages, scan_menu_pages
from quick_webapp.auth.basic.user import User
from quick_webapp.auth.basic.user_service import UserService
from quick_webapp.auth.basic.curent_user_service import CurrentUserService, scan_pages_permissions, filter_current_user_menu_pages
from quick_webapp.auth.basic.data_source_impl.sqlite import SQLiteUserDataSource

def terminate_app():
    ensure_shutdown_hook_holder("default").terminate()
    os.kill(os.getpid(), signal.SIGTERM)

@bean
def menu_handlers() -> dict[str, Callable]:
    return {
        "home": lambda: st.switch_page(home_page()),
        "logout": lambda: current_user_service().logout(),
        "exit": terminate_app
    }


#in doc
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
    return "a_session_id_key"

@bean
def ui_package() -> Path:
    return Path(__file__).parent / "page"

@bean
def home_page() -> str:
    return ui_package() / "home.py"

@bean
def login_page() -> str:
    return ui_package() / "login.py"

@bean
def service_pages() -> list[Path]:
    return scan_service_pages(ui_package())

@bean
def menu_pages() -> dict[str, dict[str, Path]]:
    return scan_menu_pages(ui_package(), mapper="token_underscore")

@bean
def page_permissions() -> dict[Path, list[str] | None]:
    return scan_pages_permissions(ui_package())

@session_bean
def user_menu_pages() -> dict[str, dict[str, Path]]:
    return filter_current_user_menu_pages(menu_pages(), current_user_service(), page_permissions())

@bean
def user_service() -> UserService:
    data_source = SQLiteUserDataSource(
        ["user", "admin"],
        "users.db"
    )

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
        lambda user_input, password: user_input == password
    )

@bean
def current_user_service() -> CurrentUserService:
    return CurrentUserService(
        user_service(),
        login_page=login_page(),
        no_permision_page=home_page(),
        session_id_key=session_id_key()
    )
``````

## page: UI

### action_table.py
 ``````python
import streamlit as st

from quick_webapp.webapp import menu_page
from quick_webapp.util.ui import action_table
from config import webapp


class OrderExample:
    def __init__(self, title: str, amount: int, price: float):
        self._title = title
        self._amount = amount
        self._price = price

    @property
    def title(self) -> str:
        return self._title

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def price(self) -> float:
        return self._price


orders = [
    OrderExample("Apple", 3, 1.25),
    OrderExample("Banana", 5, 0.80),
    OrderExample("Orange", 2, 1.60),
]


def edit(order: OrderExample):
    st.info(f"Edit: {order.title}")


def delete(order: OrderExample):
    st.warning(f"Delete: {order.title}")


web_app = webapp()
menu_page("1_UIs", "3_Action table")

st.write("**Orders:**")

action_table(
        data=orders,
        data_mappers={
            "Title": lambda o: st.write(o.title),
            "Amount": lambda o: st.write(str(o.amount)),
            "Price": lambda o: st.write(f"${o.price:.2f}"),
            "Total": lambda o: st.write(f"${o.amount * o.price:.2f}")
        },
        action_mappers={
            "Edit": edit,
            "Delete": delete,
        },
        actions_col_label="Actions",
        data_to_action_column_ratios=[6, 2, 2, 1, 1],
        container_width=1000
)

web_app.at_page_end()
``````

### admin_page.py
 ``````python
import streamlit as st
from quick_webapp.webapp import menu_page
from config import webapp
from config import current_user_service

current_user_service = current_user_service()

current_user_service.only_permitted("admin")
menu_page("9_Admin", "1_Welcome, Admin")

web_app = webapp()
web_app.at_page_beginning("This is an admin page title")

st.write("**You are an admin**")
if st.button("Exit", type="primary"):
    current_user_service.logout()

web_app.at_page_end()
``````

### extended_menu_page.py
 ``````python
import streamlit as st
from quick_webapp.webapp import menu_page
from quick_webapp.webapp import menu_page
from config import webapp, ui_package, login_page

@st.cache_resource
def go_to_simple_page():
    return lambda: st.switch_page(ui_package() / "simple_page.py")

@st.cache_resource
def go_login():
    return lambda: st.switch_page(login_page())

web_app = webapp()
menu_page("1_UIs", "2_Extended menu")

web_app.at_page_beginning("This is an extended page title", {"To simple page": go_to_simple_page(), "Go login": go_login()})

st.write("Click on addition button in the menu: **To simple page**")
st.write("Or click **Go login**")

web_app.at_page_end()
``````

### home.py
 ``````python
import streamlit as st
from quick_webapp.util.ui import restart_browser_window
from config import current_user_service
from config import webapp
from quick_webapp.webapp import menu_page, service_page

menu_page("0_Home", "0_Home")

current_user_service = current_user_service()
current_user_service.only_permitted()

if st.query_params.get("reload"):
    st.query_params.clear()
    # to restart the streamlit session
    restart_browser_window()

web_app = webapp()
web_app.at_page_beginning()
user = current_user_service.get_user()

st.header(f"Welcome to Quick WebApp Example, **{user.user_name}**!")
``````

### login.py
 ``````python
import streamlit as st
from quick_webapp.auth.basic.ui_form import login_form, registration_form, set_password_form
from quick_webapp.util.ui import read_cookie, get_browser_locate, get_browser_timezone
from quick_webapp.webapp import service_page
from config import webapp, user_service, session_id_key, home_page

service_page()
user_service = user_service()

web_app = webapp()

web_app.at_page_beginning("Login")
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
        
web_app.at_page_end()
``````

### simple_page.py
 ``````python
import streamlit as st
from quick_webapp.webapp import menu_page
from config import webapp

menu_page("1_UIs", "1_Simple page")

web_app = webapp()
page_session_obj = web_app.page_session_object()

web_app.at_page_beginning(page_title="A simple page", page_title_render=lambda t: st.subheader(t))

text_input = st.text_area("Type the text:")

if text_input and len(text_input):
    page_session_obj["last_text"] = text_input

text_input = page_session_obj.get("last_text")
if text_input:
    st.write("**You typed:**")
    st.write(text_input)

web_app.at_page_end(["console.log('print to browser!');"])
``````

### user_management/all_users.py
 ``````python
import streamlit as st
from quick_webapp.webapp import menu_page, WebApplication
from quick_webapp import bean
from quick_webapp.util.ui import action_table
from quick_webapp.auth.basic.user_service import UserService
from quick_webapp.auth.basic.ui_form import manage_user_form, edit_user_form
from config import webapp
from config import current_user_service, user_service

@bean("all_users_data_mapper")
def data_mappers() -> dict[str, callable]:
    return {
        "Username": lambda user: st.write(f"**{user.user_name}**"),
        "Name": lambda user: st.write(user.name if user.name else ':color[Not set]{foreground="#6b6b6b" background="#e3e3e3"}'),
        "Roles": lambda user: st.write(" ".join(f':color[{role}]{{foreground="#f5fffa" background="#464bb4"}}' for role in user.roles)),
        "Locked": lambda user: st.write("🔴" if user.locked else "⚪")
    }

def switch_user_lock(user):
    user_service.update_user_lock(user.user_name, not user.locked)
    webapp().page_session_object()["modified"] = True
    st.rerun()

def edit_user(user):
    webapp().page_session_object()["modified"] = True
    edit_user_form(user.user_name, user_service)

@bean("all_users_action_mapper")
def action_mappers() -> dict[str, callable]:
    return {
        "🔒": switch_user_lock,
        "📝": edit_user
    }

current_user_service = current_user_service()
user_service: UserService = user_service()

current_user_service.only_permitted("admin")
menu_page("9_User Management", "1_All")

current_user_name = current_user_service.get_user().user_name

web_app: WebApplication = webapp()
session = web_app.page_session_object()
web_app.at_page_beginning("User Management | All", page_title_render=lambda title: st.subheader(title))

users_per_page = 10

with st.container(horizontal=True, vertical_alignment="bottom"):
    q_user_name = st.text_input("User name:", "", width=350)
    if st.button("Search", type="primary") or "q_user_name" not in session:
        session["q_user_name"] = q_user_name
        session["offset"] = 0
        session["page"] = user_service.fetch_users(q_user_name, 0, users_per_page, current_user_name)
        session["has_next"] = len(session["page"]) == users_per_page and len(user_service.fetch_users(q_user_name, users_per_page, 1, current_user_name)) > 0

if "page" in session:
    page = session["page"]
    offset = session.get("offset", 0)

    if session.get("modified"):
        page = user_service.fetch_users(q_user_name, offset, users_per_page, current_user_name)
        session["modified"] = False
        session["page"] = page


    if page:
        st.write("**Users:**")
        action_table(
            page,
            data_mappers(),
            action_mappers(),
            container_width=800,
            data_to_action_column_ratios=[1, 1.2, 1, 0.4, 0.2, 0.2]
        )

        has_next = session.get("has_next")
        has_previous = offset > 0

        if has_next or has_previous:
            clicked = False
            with st.container(horizontal=True):
                if has_previous:
                    if st.button("<"):
                        clicked = True
                        offset = offset - users_per_page
                        session["offset"] = 0 if offset < 0 else offset

                if has_next:
                    if st.button(">"):
                        clicked = True
                        offset = offset + users_per_page
                        session["offset"] = offset
            
            if clicked:
                session["page"] = user_service.fetch_users(q_user_name, offset, users_per_page, current_user_name)
                session["has_next"] = len(session["page"]) == users_per_page and len(user_service.fetch_users(q_user_name, offset + users_per_page, 1, current_user_name)) > 0
                st.rerun()
    else:
        st.write(f"*No users like '{q_user_name}', honey!*")

web_app.at_page_end()
``````

### user_management/current_users.py
 ``````python
import streamlit as st
from quick_webapp.webapp import menu_page
from quick_webapp import bean
from quick_webapp.util.ui import action_table
from quick_webapp.auth.basic.user_service import UserService
from quick_webapp.auth.basic.ui_form import manage_user_form, edit_user_form
from config import webapp
from config import current_user_service, user_service

current_user_service = current_user_service()
user_service: UserService = user_service()

current_user_service.only_permitted("admin")
menu_page("9_User Management", "1_Current")


current_user_name = current_user_service.get_user().user_name

web_app = webapp()
web_app.at_page_beginning("User Management | Current", page_title_render=lambda title: st.subheader(title))

@bean("current_users_data_mapper")
def data_mappers() -> dict[str, callable]:
    return {
        "Username": lambda user_session: st.write(f"**{user_session[0].user_name}**"),
        "Name": lambda user_session: st.write(user_session[0].name if user_session[0].name else ':color[Not set]{foreground="#6b6b6b" background="#e3e3e3"}'),
        "Roles": lambda user_session: st.write(" ".join(f':color[{role}]{{foreground="#f5fffa" background="#464bb4"}}' for role in user_session[0].roles)),
        "Sessions": lambda user_session: st.write(len(user_session[1]))
    }

def manage_user(user_session):
    webapp().page_session_object()["modified"] = True
    manage_user_form(user_session[0].user_name, user_service)

def edit_user(user_session):
    webapp().page_session_object()["modified"] = True
    edit_user_form(user_session[0].user_name, user_service)

@bean("current_users_action_mapper")
def action_mappers() -> dict[str, callable]:
    return {
        "🧑‍💼": manage_user,
        "📝": edit_user
    }

current_users = user_service.get_all_user_sessions(current_user_name)

if current_users:
    st.write("**Active users:**")
    action_table(
        current_users.items(),
        data_mappers(),
        action_mappers(),
        container_width=800,
        data_to_action_column_ratios=[1, 1.2, 1, 0.4, 0.2, 0.2]
    )
else:
    st.write("*No active users to manage...*")


web_app.at_page_end()
``````
