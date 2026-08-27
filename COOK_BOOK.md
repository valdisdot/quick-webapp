## Cook book & How-to-Build

### I. Context and Session

#### 1. The bean

**Q:** How to make an object that lives in the application scope? (A singleton)

**A1:** Define decorated with `@bean` fuction and then call it.

``````python
from quick_webapp import bean

# a singleton object with key my_object
@bean
def my_object() -> Any:
    return {}

# a singleton object with key another_object
@bean("another_object")
def other_object() -> Any:
    return {}

# then in other part of code
my_object()
other_object()
``````

**A2:** Use function `ensure_object` and provide a factory method to it.

``````python
def factory():
    return {}

# then in other part of code
from quick_webapp import ensure_object

ensure_object("my_object", factory)
``````

**Q:** How to make an object that lives in a session scope?

**A1:** Define decorated with `@session_bean` fuction and then call it.

``````python
from quick_webapp import session_bean

# a session object with key my_object
@session_bean
def my_session_object() -> Any:
    return {}

# a session object with key another_object
@session_bean("another_session_object")
def other_session_object() -> Any:
    return {}

# then in other part of code
my_session_object()
other_session_object()
``````

**A2:** Use function `ensure_session_object` and provide a factory method to it.

``````python
def factory():
    return {}

# then in other part of code
from quick_webapp import ensure_session_object

ensure_session_object("my_session_object", factory)
``````

### II. Web application

#### 1. Initialization

**Q:** How to properly initialize the WebApplication object?

**A:** Ideally, as a singleton since the WebApplication object is basically a holder for the content of javascript, css and icon from webapp directory. Example below is self-explanatory.

``````python
from quick_webapp import bean
from quick_webapp.webapp import WebApplication

@bean
def webapp() -> WebApplication:
    return WebApplication(
        header_menu={"Exit": "my_exit_command"},
        header_menu_command_handlers={"my_exit_command": lambda: os.kill(os.getpid(), signal.SIGTERM)},
        header_buttons_width=150,
        header_buttons_gap=10,
        webapp_dir="webapp"        
    )
``````

#### 2. A simple page

**Q:** What is the typical WebApplication usage inside the UI page code?

**A:** Code must call `at_page_beginning` before any UI elements are defined to load css from webapp, optionally with page_title and page_title_render callable, additional header_menu (specific for current page) and styles (a list of css strings)

After all UI elements are defined, the `at_page_end` must be called to add javascript to the page, optionally with custom js (a list of javascript strings)

Additionally, the `page_session_object` can be called to get a session object that is specific for current page.

``````python
import streamlit as st
from quick_webapp.webapp import WebApplication
from my_app.config import webapp

web_app: WebApplication = webapp()
page_session_obj: dict[Any, Any] = web_app.page_session_object() # or WebApplication.page_session_object()

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

#### 3. A starter file and sidebar automagic

**Q1:** Since each Streamlit page must be registered (with streamlit.navigation), how to register all my UI pages?

**A:** webapp.py contains standardized method `streamlit_page` that returns a `streamlit.StreamlitPage`, which then you use in your starter file (with `streamlit run my_main.py`).

**menu_pages_tree** is expected to be a dictionary where key is a sidebar menu label, value is either page (str or Path) or a submenu, which is also a dict but value can be only a page (str or Path)

**service_pages** is expected to be a list of pages (str or Path) that must be registered to be accessible but not be present on the sidebar.

``````python
from quick_webapp.webapp import WebApplication, streamlit_page
# assuming menu_pages() and service_pages() return appropriate data structrure
from my_app.config import webapp, user_menu_pages, service_pages

web_app: WebApplication = webapp()
streamlit_page = streamlit_page(
    menu_pages_tree=menu_pages(), # is either dict[str, str | Path | dict[str, str | Path]] or None
    service_pages=service_pages(),     # is either list[str | Path] or None
    initial_page_title="Main"          # is either str or None
)
streamlit_page.run()
``````

**Q2:** Does it mean I have to build and define somewhere those menu dictionary and service pages list?

**A:** Partitionally - you have to provide the structures but use `scan_menu_pages` and `scan_service_pages` to fetch page Paths that marked respectfully with `menu_page` and `service_page` dull methods.

- In UI page that must be placed in sidebar:

``````python
from quick_webapp.webapp import menu_page

menu_page(section_name="Report", subsection_name="Sales")

# other UI code
``````

- In UI page that must be just registered:

``````python
from quick_webapp.webapp import service_page

service_page()

# other UI code
``````

- Scan for menu pages (caching is recomended since it scans .py files but it's up to you):

``````python
from quick_webapp import bean
from quick_webapp.webapp import scan_menu_pages

@bean
def menu_pages():
    return scan_menu_pages(
        ui_package_root=Path(__file__).parent,
        "ui", "pages",
        # "sort" to simple a-Z section and subsection labels sort
        # "token_underscore" to use the token before the first underscore (_) in section and subsection labels as sort value, e.i. for menu_page(section_name="9_Report", subsection_name="2_Sales")
        mapper="sort" 
    )

@bean
def service_pages():
    return scan_service_pages(
        ui_package_root=Path(__file__).parent,
        "ui", "pages"
    )
``````

- Filter if needed (for example, make it user specific - see Basic User) and use with `streamlit_page` as offered in the example in answer to Q1 in this section.

#### 4. util.ui

**Q:** What is ui.py for?

**A:** The util is used inside the WebApplication but all fuctions also accesible to use.

Some of them are wrappers around standard Streamlit code like `render_branched_fragment()`, others are a javascript snippets that get injected in user's window like `execute_javascript()`. Also, there are helpers to render data.

- Example of rendering a `util.data.data_view.DataView` using universal `render()`

``````python
from quick_webapp.util.data.data_view import DataView
from quick_webapp.util.ui import render
from my_app.service import fetch_users_data_view

render(fetch_users_data_view())

``````

- Example of rendering a `DataFrame` from a spreadsheet interface of `util.data.spreadsheet_view.SpreadsheetView`

``````python
from quick_webapp.util.data.spreadsheet_view import SpreadsheetView
from quick_webapp.util.ui import render
from my_app.service import fetch_users_spreadsheet

render(fetch_users_spreadsheet().get_data_frame(0))
``````

- Example usage of `action_table`

``````python
import streamlit as st
from quick_webapp.util.ui import action_table
from my_app.entity import OrderExample

orders = [
    OrderExample("Apple", 3, 1.25),
    OrderExample("Banana", 5, 0.80),
    OrderExample("Orange", 2, 1.60),
]

def edit(order: OrderExample):
    st.info(f"Edit: {order.title}")

def delete(order: OrderExample):
    st.warning(f"Delete: {order.title}")


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
``````

### III. User, UserService and CurrentUserService

**Q:** Does library offer any user management and UI for it?

**A:** Yes, it has the `auth.basic` package with functions and classes for user management, data source and UI forms (registration, set password, edit etc.).

User is an entity (logically, physically is a DTO), initialization flow is:

CurrentUserService --(accepts)--> UserService --(accepts)--> UserDataSource

UserDataSource is an interface, `data_source_impl` offers ready to use sqlite and in-file implementations.

Initialization flow example with SQLiteUserDataSource and some test users

``````python
from quick_webapp.auth.basic.user_service import UserService
from quick_webapp.auth.basic.curent_user_service import CurrentUserService
from quick_webapp.auth.basic.data_source import UserDataSource
from quick_webapp.auth.basic.data_source_impl.sqlite import SQLiteUserDataSource

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
def data_source() -> UserDataSource:
    return SQLiteUserDataSource(
        predefined_roles=["user", "admin"],
        db_path="users.db"
    )

@bean
def user_service() -> UserService:
    data_source = data_source()

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
        user_data_source=data_source,
        password_hash_function=lambda password: password,
        password_hash_check_function=lambda user_input, password: user_input == password
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

