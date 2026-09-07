from __future__ import annotations

from typing import Any, Literal
from collections.abc import Callable
import os
import re
from uuid import uuid4
from pathlib import Path
import streamlit as st
from streamlit.navigation.page import StreamlitPage
from quick_webapp import ensure_session_object
from quick_webapp.util.ui import apply_css, execute_javascript
from quick_webapp.util.reflection import scan_params


def menu_page(section_name: str, subsection_name: str):
    """
    Marker method to apply automagic for menu builder.
    Used to scan .py UI files to build an application menu.

    Like:

    section_name
    - subsection_name
    - subsection_name
    - and so on
    """

    pass

def service_page():
    """
    Marker method to apply automagic for registering Streamlit pages that are NOT to be in navigation sidebar.
    """

    pass

def scan_menu_pages(
    ui_package_root: str | Path,
    *ui_package_path: str,
    mapper: Literal["sort", "token_underscore"] | Callable[[list[str]], list[str]] = "sort"
) -> dict[str, dict[str, Path]]:
    """
    Scans all .py files for menu_page(...) calls and builds a sidebar tree.natural

    Only the first menu_page() call in each file is used.

    mapper function is used to process scanned items, if mapper is a string, two option is available:

    - sort for a natural string sorting 1-9-a-Z
    - token_underscore for a sort by a order token before underscore ("2_Welcome Page", "1_Home", ... , "14_Admin Page" will be mapped as "Home", "Welcome Page", ..., "Admin Page") 
    """

    menu_items: dict[str, dict[str, Path]] = {}

    menu_page_calls = scan_params(
        "menu_page",
        ui_package_root,
        *ui_package_path,
    )

    for file, calls in menu_page_calls.items():
        if not calls:
            continue

        first = calls[0]

        args = first["args"]
        kwargs = first["kwargs"]

        section_name = None
        subsection_name = None

        if len(args) >= 1:
            section_name = args[0]

        if len(args) >= 2:
            subsection_name = args[1]

        section_name = kwargs.get("section_name", section_name)
        subsection_name = kwargs.get("subsection_name", subsection_name)

        if not section_name or not subsection_name:
            raise ValueError(
                f"Invalid menu_page() in {file}: "
                f"section_name={section_name!r}, "
                f"subsection_name={subsection_name!r}"
            )

        section = menu_items.setdefault(section_name, {})

        if not isinstance(section, dict):
            raise ValueError(f"Section '{section_name}' already exists as a page")

        section[subsection_name] = file
    
    mapper = (
        __sort
        if mapper is None or mapper == "sort"
        else (
            __token_underscore
            if mapper == "token_underscore"
            else (mapper if callable(mapper) else __sort)
        )
    )

    return mapper(menu_items)

def __sort(items: dict[str, dict[str, Path]]) -> dict[str, dict[str, Path]]:
    sorted_items = {}
    for k, subitems in sorted(items.items()):
        sorted_items[k] = dict(sorted(subitems.items()))
    return sorted_items

def __token_underscore(
    items: dict[str, dict[str, Path]]
) -> dict[str, dict[str, Path]]:
    def parse(name: str) -> tuple[int, str]:
        m = re.match(r"^(\d+)_(.+)$", name)
        if m:
            return int(m.group(1)), m.group(2)

        return float("inf"), name

    result: dict[str, dict[str, Path]] = {}

    for section_name, subitems in sorted(
        items.items(),
        key=lambda item: parse(item[0]),
    ):
        _, clean_section_name = parse(section_name)

        result[clean_section_name] = {
            parse(subsection_name)[1]: path
            for subsection_name, path in sorted(
                subitems.items(),
                key=lambda item: parse(item[0]),
            )
        }

    return result

def scan_service_pages(
    ui_package_root: str | Path,
    *ui_package_path: str,
) -> list[Path]:
    """
    Scans all .py files for service_page() calls.

    Only the presence of at least one service_page() call matters.
    """

    service_pages: list[Path] = []

    service_page_calls = scan_params(
        "service_page",
        ui_package_root,
        *ui_package_path,
    )

    for file, calls in service_page_calls.items():
        if calls: 
            service_pages.append(file)

    return service_pages

def streamlit_page(
    menu_pages_tree: dict[str, str | Path | dict[str, str | Path]],
    service_pages: list[str | Path] = None,
    initial_page_title: str | None = None,
) -> StreamlitPage:
    """
    Creates and return a Streamlit navigation page.

    Configures the sidebar navigation tree and sets the browser tab
    title and app icon.

    menu_pages_tree can be:
    - a manually build menu dictionary
    - automagic menu from scan_menu_items()
    - user-centric menu, filtered with allowed pages list from auth.base.current_user_service.CurrentUserService.get_allowed_user_pages()

    Same applied to service_pages.

    Since Streamlit rerun script and this method will called multible times, the view reloads each time.

    Also, registers service pages so the flow can switch to them.
    """

    sidebar_menu = {}
    for label, page_or_submenu in menu_pages_tree.items():
        submenu = []
        sidebar_menu[label] = submenu
        if isinstance(page_or_submenu, dict):
            for submenu_label, submenu_page in page_or_submenu.items():
                submenu.append(st.Page(page=submenu_page, title=submenu_label))
        else:
            submenu.append(st.Page(page=page_or_submenu, title=label))

    if service_pages:
        service_pages_list = []
        sidebar_menu["hidden"] = service_pages_list
        for service_page in service_pages:
            service_pages_list.append(st.Page(page=service_page, visibility="hidden"))

    st.set_page_config(
        page_title=initial_page_title, layout="wide", initial_sidebar_state="auto"
    )

    pg = st.navigation(sidebar_menu, position="sidebar", expanded=False)

    return pg

def streamlit_main_sctipt_path() -> Path:
    """
    Returns Streamlit main script path that was used with streamlit run command.
    """

    return Path(st.config._main_script_path).resolve()


class WebApplication:
    """
    Web application wrapper that loads shared CSS/JS and provides a
    simple framework for building Streamlit pages with a header and sidebar.
    """

    @classmethod
    def __load_webapp__(cls, dir: str, webapp_object: dict = None):
        """
        Recursively load CSS, JavaScript and the app icon from ``dir``.

        Files with extensions ``.css`` and ``.js`` are appended to the
        corresponding lists; a file named ``icon.*`` is used as the app icon.
        """

        webapp = {"css": [], "js": []} if webapp_object is None else webapp_object

        if os.path.exists(dir) and os.path.isdir(dir):
            for filename in sorted(
                os.listdir(dir),
                key=lambda name: (os.path.isdir(os.path.join(dir, name)), name.lower()),
            ):
                file_path = os.path.join(dir, filename)

                if os.path.isfile(file_path):
                    extension = os.path.splitext(filename)[1].lower()

                    if extension == ".js":
                        with open(file_path) as js:
                            webapp["js"].append("".join(js.readlines()))
                    elif extension == ".css":
                        with open(file_path) as css:
                            webapp["css"].append("".join(css.readlines()))
                    elif os.path.splitext(filename)[0].lower() == "icon":
                        webapp["icon"] = file_path

                elif os.path.isdir(file_path):
                    cls.__load_webapp__(file_path, webapp)

        return webapp

    def __init__(
        self,
        header_menu: dict[str, str | Path | Callable | dict[str, str | Path | Callable]] = None,
        header_menu_command_handlers: dict[str, Callable] = None,
        header_buttons_width: int | None = None,
        header_buttons_gap: int | None = None,
        webapp_dir="webapp",
    ):
        """

        Loads shared assets from ``webapp_dir`` and configures the default
        top header menu (labels, handlers and button sizes).

        header_menu is a dictionary that will be parsed into a header menu (2 level maximum).

        Key of the header dictionary is interpreted as a label in UI, value in case of Path type will be used to switch into it as a Streamlit page, in case of string it will be treated as a command with handler the header_menu_command_handlers. In case of the type of dict (submenu) will be parsed as the same as header_menu except the dictionary, otherwise submenues inside submenues is not supported.
        """

        self.__webapp = self.__load_webapp__(webapp_dir)
        self.__header_menu = header_menu if header_menu else {}
        self.__header_menu_command_handlers = (
            header_menu_command_handlers if header_menu_command_handlers else {}
        )
        self.__header_buttons_width = (
            header_buttons_width if header_buttons_width else 120
        )
        self.__header_buttons_gap = header_buttons_gap if header_buttons_gap else 10

    def as_context(
        self,
        page_title: str | None = None,
        header_menu: dict[str, str | Path | dict[str, str | Path]] = None,
        styles: list[str] = None,
        page_title_render: Callable[[str], Any] = None,
        java_scripts: list[str] = None
    ) -> WebApplicationContext:
        """
        Encapsulates WebApplication.at_page_beginning and WebApplication.at_page_end into the context manager, to use 'with web_app_obj.context(...): pass
        """

        return WebApplicationContext(
            self,
            page_title,
            header_menu,
            styles,
            page_title_render,
            java_scripts
        )
    
    def __build_header(self, header_menu: dict[str, str | Path | Callable | dict[str, str | Path | Callable]] = None) -> list[dict[str, Any]]:
        """
        Return a list of parsed header items.

        Item dictionary has: key, label and action, where action is either a Callable or a list (submenu). Submenue in order contains dictionaries with label and action, where action is always a Callable.

        Raises ValueError is original item type is not supported or there is no command handler was provided in header_menu_command_handlers from constructor.
        """

        res = []

        if not header_menu:
            return res
        
        for label, page_command_or_submenu in header_menu.items():
            header_item = {
                "uuid": str(uuid4()),
                "label": label
            }

            if isinstance(page_command_or_submenu, Path):
                header_item["action"] = lambda: st.switch_page(page_command_or_submenu)

            elif isinstance(page_command_or_submenu, Callable):
                header_item["action"] = page_command_or_submenu
                
            elif isinstance(page_command_or_submenu, str):
                if page_command_or_submenu in self.__header_menu_command_handlers:
                    header_item["action"] = self.__header_menu_command_handlers.get(page_command_or_submenu)
                else:
                    raise ValueError(f"No command handler for header menu command '{page_command_or_submenu}' with label {label}")
            
            elif isinstance(page_command_or_submenu, dict):
                submenu = {}

                for sublabel, subitem in page_command_or_submenu.items():

                    if isinstance(subitem, Path):
                        submenu[sublabel] = lambda: st.switch_page(subitem)
                    
                    elif isinstance(subitem, Callable):
                        submenu[sublabel] = subitem

                    elif isinstance(subitem, str):
                        if subitem in self.__header_menu_command_handlers:
                            submenu[sublabel] = self.__header_menu_command_handlers.get(subitem)
                        else:
                            raise ValueError(f"No command handler for header submenu command '{subitem}' with label {sublabel}")
                    else:
                        raise ValueError(f"Unsupported subitem type {type(subitem)} with label {sublabel}")

                header_item["action"] = submenu
            
            else:
                raise ValueError(f"Unsupported item type {type(page_command_or_submenu)} with label {label}")
            
            res.append(header_item)

        return res
    
    def __init_header(self, header_menu: dict[str, str | Path | Callable | dict[str, str | Path | Callable]] = None):
        session_storage: dict = ensure_session_object(st.context.url)
                
        if "header" not in session_storage or session_storage.get("last_header") != header_menu:            
            session_storage["last_header"] = header_menu
            
            items = dict(self.__header_menu.items())
            if header_menu: items.update(header_menu.items())

            session_storage["header"] = self.__build_header(items)
        
        i = 0
        for header_menu in reversed(session_storage["header"]):
            label = header_menu.get("label")
            uuid = header_menu.get("uuid")
            action = header_menu.get("action")

            apply_css(f"""
                .st-key-{uuid}{{
                        position: absolute;
                        top: 10px;
                        right: {self.__header_buttons_gap + i * (self.__header_buttons_width + self.__header_buttons_gap)}px;
                        z-index: 100000;
                        pointer-events: auto; 
                }}        
            """)
            i += 1

            if isinstance(action, Callable):
                if st.button(label, key=uuid, width=self.__header_buttons_width):
                    action()
            
            elif isinstance(action, dict):
                submenu = st.menu_button(label, options=action.keys(), key=uuid, width=self.__header_buttons_width)

                if submenu is not None:
                    action[submenu]()

    def at_page_beginning(
        self,
        page_title: str | None = None,
        header_menu: dict[str, str | Path | dict[str, str | Path]] = None,
        styles: list[str] = None,
        page_title_render: Callable[[str], Any] = None
    ):
        """
        Render header, base styles and the header menu at the page start.

        header_menu is expected to be the same as for the constructor of this class.

        Applies built‑in CSS reset, webapp‑level styles and optional extra
        styles, then renders header buttons for the configured header menu items.
        """

        apply_css("""
                *, *::before, *::after {
                    box-sizing: border-box;
                }

                html {
                    font-size: 16px;
                    -webkit-text-size-adjust: 100%;
                }

                body {
                    margin: 0;
                    line-height: 1.5;
                }

                div[data-testid="stComponent"] {
                    margin: 0 !important;
                    padding: 0 !important;
                }

                iframe[title="st.iframe"] {
                    display: none !important;
                }
                        
                .block-container {
                    padding-top: 4rem;
                    padding-left: 1.5rem;
                }

                input, button, textarea, select {
                    font: inherit;
                }

                img, svg {
                    display: block;
                    max-width: 100%;
                }

                .stApp {
                    zoom: 1;
                }

                div[data-testid="stSidebarContent"] {
                    border-right: 1px solid #CBD5E1;
                }

                header.stAppHeader {
                    background: #e9edf2;
                    border-bottom: 1px solid #CBD5E1;
                    z-index: 99999;
                    pointer-events: none;
                }
                        
                button[kind="headerNoPadding"] {
                    width: 50px;
                    height: 40px;
                }
            """)

        st.set_page_config(page_title=page_title, page_icon=self.__webapp.get("icon"))

        for css in self.__webapp["css"]:
            apply_css(css)

        if styles and isinstance(styles, list):
            for css in styles:
                apply_css(css)

        self.__init_header(header_menu)

        if page_title_render and isinstance(page_title_render, Callable):
            page_title_render(page_title)

    def at_page_end(self, java_scripts: list[str] = None):
        """
        Inject JavaScript at the end of the page.

        Executes scripts loaded from the webapp directory and any
        additional scripts passed in ``java_scripts``.
        """

        for js in self.__webapp["js"]:
            execute_javascript(js)

        if java_scripts and isinstance(java_scripts, list):
            for js in java_scripts:
                execute_javascript(js)

class WebApplicationContext:
    """
    Helper class that encapsulates WebApplication.at_page_beginning and WebApplication.at_page_end into the context manager, to use 'with web_app_obj.context(...): pass'
    """

    def __init__(
            self, 
            webapp: WebApplication,
            page_title: str | None = None,
            header_menu: dict[str, str | Path | dict[str, str | Path]] = None,
            styles: list[str] = None,
            page_title_render: Callable[[str], Any] = None,
            java_scripts: list[str] = None
        ):
        self.__webapp = webapp
        self.__page_title = page_title
        self.__header_menu = header_menu
        self.__styles = styles
        self.__page_title_render = page_title_render
        self.__java_scripts = java_scripts

    def __enter__(self):
        self.__webapp.at_page_beginning(self.__page_title, self.__header_menu, self.__styles, self.__page_title_render)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__webapp.at_page_end( self.__java_scripts)