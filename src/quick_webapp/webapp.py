from typing import Any
from collections.abc import Callable
import os
from uuid import uuid4
import streamlit as st
from streamlit.navigation.page import StreamlitPage
from quick_webapp import page_session_bean
from quick_webapp.util.ui import apply_css, execute_javascript

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
                key=lambda name: (
                    os.path.isdir(os.path.join(dir, name)),
                    name.lower()
                )
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

    def __init__(self, 
                 menu: dict[str, str | dict[str, str]] = None, 
                 menu_coomand_handlers: dict[str, Callable] = None,
                 buttons_width: int | None = None, 
                 buttons_gap: int | None = None, 
                 webapp_dir = "webapp"
                 ):
        """
        Create a :class:`WebApplication`.

        Loads shared assets from ``webapp_dir`` and configures the default
        top header menu (labels, handlers and button sizes).
        """

        self.__webapp = self.__load_webapp__(webapp_dir)
        self.__menu = menu if menu else {}
        self.__menu_coomand_handlers = menu_coomand_handlers if menu_coomand_handlers else {}
        self.__buttons_width = buttons_width if buttons_width else 120
        self.__buttons_gap = buttons_gap if buttons_gap else 10
    
    def streamlit_page(self, 
                       page_title,
                       sidebar_tree: dict[str, str | dict[str, str]],
        ) -> StreamlitPage:
        """Create and return a Streamlit navigation page.

        Configures the sidebar navigation tree and sets the browser tab
        title and app icon.
        """

        menu = {}
        for label, page_or_submenu in sidebar_tree.items():
            submenu = []
            menu[label] = submenu
            if isinstance(page_or_submenu, dict):
                for submenu_label, submenu_page in page_or_submenu.items():
                    submenu.append(st.Page(page=submenu_page, title=submenu_label))
            else:
                submenu.append(st.Page(page=page_or_submenu, title=label))
        
        st.set_page_config(page_title, self.__webapp.get("icon"), "wide", "auto")

        pg = st.navigation(
            menu,
            position="sidebar",
            expanded=False
        )
        return pg
    
    def page_session_object(self) -> dict[str, Any]:
        """
        Returns a dictionary for current page related session.
        """

        return page_session_bean()

    def at_page_beginning(self, 
                          page_title: str | None = None, 
                          menu: dict[str, str | dict[str, str]] | None = None, 
                          styles: list[str] = None
                          ):
        """
        Render header, base styles and the top menu at the page start.

        Applies built‑in CSS reset, webapp‑level styles and optional extra
        styles, then renders header buttons for the configured menu items.
        """

        apply_css(
            """
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
        if page_title:
            st.set_page_config(page_title)

        for css in self.__webapp["css"]:
            apply_css(css)

        if styles and isinstance(styles, list):
            for css in styles:
                apply_css(css)
        
        items = menu if menu else {}
        items.update(self.__menu)

        session_storage: dict = self.page_session_object()
        if not "header_uuids" in session_storage:
            uuids = []
            session_storage["header_uuids"] = uuids
            for i in range(len(items)):
                uuids.append(str(uuid4()))

        i = -1
        for label, page_or_submenu in reversed(items.items()):
            i += 1
            uuid = session_storage["header_uuids"][i]
            apply_css(f"""
                .st-key-{uuid}, .st-key-exit {{
                        position: absolute;
                        top: 10px;
                        right: {self.__buttons_gap + i * (self.__buttons_width + self.__buttons_gap)}px;
                        z-index: 100000;
                        pointer-events: auto; 
                }}        
            """)
            if isinstance(page_or_submenu, str):
                if page_or_submenu.endswith(".py"):
                    if st.button(label, key=uuid, width=self.__buttons_width):
                        st.switch_page(page_or_submenu)
                elif page_or_submenu in self.__menu_coomand_handlers:
                    handler = self.__menu_coomand_handlers.get(page_or_submenu)
                    if handler and isinstance(handler, Callable):
                        if st.button(label, key=uuid, width=self.__buttons_width):
                            handler()
                    else:
                        raise ValueError(f"Handler for '{page_or_submenu}' menu item is not a callable")
                else:
                    raise ValueError(f"No handler for '{page_or_submenu}' menu item")

            elif isinstance(page_or_submenu, dict):
                submenu = st.menu_button(label = label, options = page_or_submenu.keys(), key = uuid, width = self.__buttons_width)
                if submenu is not None:
                    st.switch_page(page_or_submenu[submenu])
        
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



