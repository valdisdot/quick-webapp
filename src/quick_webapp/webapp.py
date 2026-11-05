from __future__ import annotations

from typing import Any, Literal, TypeAlias
from collections.abc import Callable
import os
import re
from uuid import uuid4
from pathlib import Path
import streamlit as st
from streamlit import config as st_config
from streamlit.navigation.page import StreamlitPage
from quick_webapp import ensure_session_object
from quick_webapp.ui import apply_css, execute_javascript
from quick_webapp.util.reflection import scan_params

def menu_page(*args, path: str | None = None, label: str | None = None, icon: str | None = None, **kwargs):
    """
    Marker method to apply automagic for menu builder.
    Used in scan_menu_pages() that scans .py UI files to build an application menu.

    path must be '/' separate path to the parent subitem

    label is the menu item itself

    icon is either an emogji or a Google material signature (":material/icon_name:") that will be passed to streamlit.Page on parsing

    Like:

    path
    [icon] label
    [icon] label
    ... and so on
    """
    pass

def menu_item(id: str | None = None):
    """
    Marker method to apply automagic for menu assembler.
    Used in assemble_menu_pages() that scans .py UI files to fill its map of the application menu.

    id is a menu identifier that will be used in a menu assembly and must not be in: 'label', 'icon', 'items'
    """
    pass

def service_page():
    """
    Marker method to apply automagic for registering Streamlit pages that are NOT to be in navigation sidebar.
    """
    pass


def __natural_key(name: str) -> tuple:
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in re.split(r"(\d+)", name)
    )


def __token_key(name: str) -> tuple:
    match = re.match(r"^(\d+)_(.+)$", name)

    if match:
        return (0, int(match.group(1)), match.group(2).casefold())

    return (1, name.casefold())


def __clean_token(name: str) -> str:
    match = re.match(r"^\d+_(.+)$", name)
    return match.group(1) if match else name

MenuTree: TypeAlias = dict[str | None, "MenuTree | st.Page"]

def __sort_tree(
    tree: MenuTree,
    *,
    token_underscore: bool = False
) -> MenuTree:
    key = __token_key if token_underscore else __natural_key
    result: MenuTree = {}

    if None in tree:
        result[None] = tree[None]

    names = (name for name in tree if name is not None)

    for name in sorted(names, key=key):
        value = tree[name]
        clean_name = __clean_token(name) if token_underscore else name

        if isinstance(value, dict):
            result[clean_name] = __sort_tree(
                value,
                token_underscore=token_underscore,
            )
        else:
            result[clean_name] = value

    return result

def scan_menu_pages(
    ui_package_root: str | Path,
    *ui_package_path: str,
    mapper: Literal["sort", "token_underscore"] | Callable[[MenuTree], MenuTree] = "sort"
) -> MenuTree:
    """
    Scans all .py files for menu_page(...) calls and builds a sidebar tree.

    Only the first menu_page() call in each file is used.

    mapper function is used to process scanned items, if mapper is a string, two option is available:

    - sort for a natural string sorting 1-9-a-Z
    - token_underscore for a sort by a order token before underscore ("2_Welcome Page", "1_Home", ... , "14_Admin Page" will be mapped as "Home", "Welcome Page", ..., "Admin Page") 
    - in case of Callable uses prividen mapper to sort

    Mapper options:
        "sort": natural sorting at every level
        "token_underscore": sort by numeric prefixes and strip them
        Callable: custom tree mapper

    A directory that is also a page stores its own Path under the None key.
    The None key is always sorted first.
    """
    menu_items: MenuTree = {}

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

        path = []
        label = None
        icon = None

        if args:
            path.extend(args[:-1])
            label = args[-1]

        if kwargs:
            if "path" in kwargs:
                path = kwargs["path"]

                if not isinstance(path, str):
                    raise ValueError(f"menu_page() path must be a string in {file}")

                path = path.split("/") if path else []

            if "label" in kwargs:
                label = kwargs["label"]

            if "icon" in kwargs:
                icon = kwargs["icon"]

        if not isinstance(label, str) or not label:
            raise ValueError(f"Invalid menu_page() label in {file}: {label!r}")

        if any(not isinstance(level, str) or not level for level in path):
            raise ValueError(f"Invalid menu_page() path in {file}: {path!r}")

        full_path = [*path, label]
        node = menu_items

        for level in full_path[:-1]:
            existing = node.get(level)

            if existing is None:
                existing = {}
                node[level] = existing
            elif not isinstance(existing, dict):
                existing = {None: existing}
                node[level] = existing

            node = existing

        leaf = full_path[-1]

        if leaf not in node:
            node[leaf] = st.Page(file, icon=icon)
        else:
            existing = node[leaf]

            if isinstance(existing, dict):
                if None in existing:
                    raise ValueError(f"Duplicate directory page '{leaf}' in {file}")

                existing[None] = st.Page(file, icon=icon)
            else:
                raise ValueError(f"Duplicate menu page '{leaf}' in {file}")


    if mapper == "sort":
        return __sort_tree(menu_items)

    if mapper == "token_underscore":
        return __sort_tree(menu_items, token_underscore=True)

    if callable(mapper):
        return mapper(menu_items)

    raise ValueError(f"Unknown mapper: {mapper!r}")

MenuSkeleton: TypeAlias = dict[str, "MenuSkeleton | str"]
__RESERVED_MENU_IDS = {"label", "icon", "items"}

def __validate_assemble_parts(
    skeleton: MenuSkeleton,
    scanned: dict[str, object],
    referenced_ids: set[str]
) -> set[str]:

    if not skeleton: 
        raise ValueError("Value must not be null or empty")

    for key, value in skeleton.items():
        if key is None:
            raise ValueError("None key is not allowed as a MenuSkeleton key.")

        if not isinstance(value, dict):
            raise ValueError(f"value for key '{key!r}' has type '{type(value)}', only 'dict' is allowed.")

        if key in scanned:
            params = list(value.keys())
            if "label" in params: params.remove("label")
            if "icon" in params: params.remove("icon")

            if params:
                raise ValueError(f"Excessive keys nor inner pages for key '{key!r}' in its config dictionary value are not allowed since the key is an ID in {scanned[key]}, keys [{', '.join(params)}].")
            
            referenced_ids.add(key)

        else:
            __validate_assemble_parts(value, scanned, referenced_ids)

    return referenced_ids

def __build_tree(
    skeleton: MenuSkeleton,
    scanned: dict[str, Path]
) -> MenuTree:
    result: MenuTree = {}

    for key, value in skeleton.items():
        label = value.get("label", key)
        icon = value.get("icon")

        if key in scanned:
            result[label] = st.Page(
                scanned[key],
                icon=icon
            )
        else:
            result[label] = __build_tree(value, scanned)

    return result

def assemble_menu_pages(
    skeleton: MenuSkeleton,
    ui_package_root: str | Path,
    *ui_package_path: str
) -> MenuTree:
    """
    Scan menu_item() calls and assemble a recursive sidebar tree.

    By default, id gets fetched from the file name (without extension so user code just call the method without args), then first arg overrides the value, then kwarg with name 'id' overrides the value.

    Skeleton rules:
    - A dictionary key found in the scanned IDs represents a page.
    - A dictionary key NOT found in the scanned IDs represents a directory.
    - Dict values configure 'label', 'icon' and 'items' (in case of dicrectory).
    - IDs may appear multiple times in the skeleton.

    Example of menu page (leaf) of MenuSkeleton element:

    {
        ...
        "the_page_id": {
            "label": "The Page",
            "icon": "💡"
        }
        ...
    }

    Example of menu directory (node) of MenuSkeleton element:

    {
        ...
        "The directory": {
            ...
            "an_id": {...},
            "Inner directory": {...}
            ...
        }
        ...
    }

    Raises ValueError for duplicate scanned IDs, unused scanned IDs, invalid configuration, or reserved IDs.
    """

    menu_item_calls = scan_params(
        "menu_item",
        ui_package_root,
        *ui_package_path
    )

    scanned: dict[str, Path] = {}

    for file, calls in menu_item_calls.items():
        if not calls:
            continue

        call = calls[0]
        args = call["args"]
        kwargs = call["kwargs"]

        item_id = file.stem
        item_id = args[0] if args else item_id
        item_id = kwargs.get("id") if "id" in kwargs else item_id

        if not item_id or not isinstance(item_id, str):
            raise ValueError(f"Invalid menu_item() ID in {file}: {item_id!r}")

        if item_id in __RESERVED_MENU_IDS:
            raise ValueError(f"Reserved menu_item() ID {item_id!r} in {file}")

        if item_id in scanned:
            raise ValueError(f"Duplicate menu_item() ID {item_id!r} or file name collision if ID argument was not been used, with {scanned[item_id]} and {file}")

        scanned[item_id] = file

    unused_ids = scanned.keys() - __validate_assemble_parts(skeleton, scanned, set())

    if unused_ids:
        details = "\n".join(f"'{menu_id!r}' in {scanned[menu_id]}" for menu_id in sorted(unused_ids))
        raise ValueError(f"Scanned menu_item(id) IDs not used by skeleton:\n{details}")

    return __build_tree(skeleton, scanned)

def scan_service_pages(
    ui_package_root: str | Path,
    *ui_package_path: str
) -> list[st.Page]:
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
            service_pages.append(st.Page(file))

    return service_pages


def __collect_pages(tree: MenuTree, target: list[st.Page]) -> None:
    if None in tree:
        page = tree[None]
        if isinstance(page, dict):
            raise ValueError("None key must contain a page, not a submenu")
        target.append(page)

    for label, value in tree.items():
        if label is None:
            continue

        if isinstance(value, dict):
            __collect_pages(value, target)
        else:
            target.append(value)

def __render_menu(parent_label: str, parent_key: str, menu_directory_item_icon: str, tree: MenuTree) -> None:
    if None in tree:
        st.page_link(
            tree[None],
            label=parent_label,
            width="stretch"
        )

    for label, page_or_dict in tree.items():
        if label is None:
            continue

        if isinstance(page_or_dict, dict):
            key = f"{parent_key}_{re.sub(r"\s", "_", label.lower())}"
            with st.expander(label, expanded=True, key=key, type="step", icon=menu_directory_item_icon):
                __render_menu(label, key, menu_directory_item_icon, page_or_dict)

        else:
            st.page_link(
                page_or_dict,
                label=label,
                width="stretch"
            )

def streamlit_page(
    menu_pages_tree: MenuTree,
    service_pages: list[st.Page],
    initial_page_title: str | None = None,
    menu_directory_item_icon: str = ":material/folder:"
) -> st.Page:
    """
    Register all menu and service pages with Streamlit and render
    a recursive sidebar using st.expander() and st.page_link().

    Directory pages are stored under the None key and rendered
    before their child pages.

    Returns the current page selected by st.navigation().
    """

    st.set_page_config(
        page_title=initial_page_title,
        layout="wide",
        initial_sidebar_state="auto",
    )

    registered_pages: list[st.Page] = list(service_pages)
    __collect_pages(menu_pages_tree, registered_pages)

    current_page = st.navigation(list({page.url_path: page for page in registered_pages}.values()), position="hidden")

    if menu_pages_tree:
        with st.sidebar:
            __render_menu("root", "sidebar", menu_directory_item_icon, menu_pages_tree)

    return current_page

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
    def __build_base_css(cls) -> str:
        config = st_config.get_config_options(force_reparse=True)
        theme_base = config.get("theme.base").value
        theme_sidebar_bg = config.get("theme.sidebar.backgroundColor").value
        theme_secondary_bg = config.get("theme.secondaryBackgroundColor").value
        sidebar_bg = theme_sidebar_bg if theme_sidebar_bg else (theme_secondary_bg if theme_secondary_bg else ("#f0f2f6" if theme_base == "light" else "#262730"))
        theme_sidebar_border_color = config.get("theme.sidebar.borderColor").value
        theme_border_color = config.get("theme.borderColor").value
        show_sidebar_border = config.get("theme.showSidebarBorder").value
        sidebar_border_on = int(show_sidebar_border) if show_sidebar_border else 0
        sidebar_border_bg = theme_sidebar_border_color if theme_sidebar_border_color else (theme_border_color if theme_border_color else ("#d6d6d6" if theme_base == "light" else "#4e4e4e"))

        return f"""
                *, *::before, *::after {{
                    box-sizing: border-box;
                }}

                html {{
                    -webkit-text-size-adjust: 100%;
                }}

                body {{
                    margin: 0;
                    line-height: 1.5;
                }}

                div[data-testid="stComponent"] {{
                    margin: 0 !important;
                    padding: 0 !important;
                }}

                iframe[title="st.iframe"] {{
                    display: none !important;
                }}
                        
                .block-container {{
                    padding-top: 4rem;
                    padding-left: 1.5rem;
                }}

                input, button, textarea, select {{
                    font: inherit;
                }}

                img, svg {{
                    display: block;
                    max-width: 100%;
                }}

                .stApp {{
                    zoom: 1;
                }}

                header.stAppHeader {{
                    background: {sidebar_bg};
                    border-bottom: {sidebar_border_on}px solid {sidebar_border_bg};
                    z-index: 99999;
                    pointer-events: none;
                }}
                        
                button[kind="headerNoPadding"] {{
                    width: 50px;
                    height: 40px;
                }}

                [data-testid="stElementContainer"]:has(.js-executor) {{
                    display: none !important;
                }}
            """

    @classmethod
    def __load_webapp(cls, dir: str, webapp_object: dict = None):
        """
        Recursively load CSS, JavaScript and the app icon from ``dir``.

        Files with extensions ``.css`` and ``.js`` are appended to the
        corresponding lists; a file named ``icon.*`` is used as the app icon.
        """

        webapp = {"css": [cls.__build_base_css()], "js": []} if webapp_object is None else webapp_object

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
                    elif os.path.splitext(filename)[0].lower() == "logo":
                        webapp["logo"] = file_path

                elif os.path.isdir(file_path):
                    cls.__load_webapp(file_path, webapp)

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

        self.__webapp = self.__load_webapp(webapp_dir)
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
        page_title_render: Callable[[str], Any] = lambda title: st.subheader(title)
    ):
        """
        Render header, base styles and the header menu at the page start.

        header_menu is expected to be the same as for the constructor of this class.

        Applies built‑in CSS reset, webapp‑level styles and optional extra
        styles, then renders header buttons for the configured header menu items.
        """

        st.set_page_config(page_title=page_title, page_icon=self.__webapp.get("icon"))

        if "logo" in self.__webapp:
            st.logo(self.__webapp["logo"], size="large")

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