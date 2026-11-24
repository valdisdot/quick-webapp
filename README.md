## quick_webapp Documentation

> A mini framework for making a quick web application in Python. Extends Streamlit library with essential tools and basic user management.


### 1. Context @bean and @session_bean

`quick_webapp`

> This library provides a mechanism for managing "beans" (objects) in two distinct scopes: **Streamlit Session Scope** (unique to each Streamlit user session) and **Global Scope** (shared across all users as singletons).


#### 1. Session-Scoped Objects

**`@session_bean(key: str | None = None)`**

> A decorator to register a function as a Streamlit session-scoped bean. The result of the function is cached and reused for every subsequent call within the same session.
> Accepts optional `key` parameter to avoid collision by fuction name.

**`ensure_session_object(session_object_key: str, _session_object_supplier: Callable[[], Any] | None = None)`**

> A direct functional call to retrieve or initialize a session-scoped object. Must provide the unique identifier for the session object and an optional function that returns the object. If omitted, returns an empty dictionary `{}`.
> Used by `@session_bean` under the hood.
> Use session-scoped objects for the page contexts like current editor state, UI-cache and other data that must be persistent during the Streamlit session (in one browser tab till the next page reload).


#### 2. Global-Scoped Objects (Singletons)

**`@bean(key: str | None = None)`**

> A decorator to register a function as a global singleton. The result is cached globally and is independent of the Streamlit runtime.
> Accepts optional `key` parameter to avoid collision by fuction name.

**`ensure_object(session_object_key: str, _session_object_supplier: Callable[[], Any] | None = None)`**

> A direct functional call to retrieve or initialize a global singleton.
> Used by `@bean` under the hood.
> Use global-scoped objects to be shared accross all aplication as the whole, with a lifetime equal the application lifetime. If used inside the logic that is not a part of a Streamlit UI application (like REST API service), ensure that you initialized both UI and services with  [st.App](https://docs.streamlit.io/1.58.0/develop/api-reference/server/st.app)


#### 3. Context management

> Functions to clear cached objects to force re-initialization.

| Function | Description |
| :--- | :--- |
| `clear_sessions_objects()` | Clears all objects stored in the Streamlit session cache. |
| `clear_objects()` | Clears all global singleton objects and their suppliers. |
| `clear()` | **Clears everything.** Wipes both Streamlit session cache and global singleton cache. |


### 2. webapp and its WebApplication

`quick_webapp.webapp`

> A collection of utilities and a framework for building Streamlit web applications, managing navigation menus, assets (CSS/JS), and a custom header component.


#### 1. WebApplication class

> A wrapper class for loading shared CSS/JS assets and providing a framework for building Streamlit pages with a header and sidebar.
>
> You use the instance (perfectly a singleton) on your every page.

*   **`constructor(header_menu: dict | None = None, header_menu_command_handlers: dict | None = None, header_buttons_width: int | None = None, header_buttons_gap: int | None = None, webapp_dir="webapp")`**

> Loads shared assets from `webapp_dir` and configures the default top header menu. Must live in context to store webapp data without reloading it from the webapp directory.

*   **`at_page_beginning(page_title: str | None = None, header_menu: dict = None, styles: list[str] = None, page_title_render: Callable[[str], Any] = lambda title: st.subheader(title))`**

> Renders the header, base styles, and the header menu at the start of the page.

*   **`at_page_end(java_scripts: list[str] = None)`**

> Injects JavaScript at the end of the page, executing scripts loaded from the webapp directory and any additional scripts provided.

*   **`as_context(page_title: str | None = None, header_menu: dict| None = None, styles: list[str] | None = None, page_title_render: Callable[[str], Any] | None = None, java_scripts: list[str] | None = None) -> WebApplicationContext`**

> Returns a `WebApplicationContext` instance to encapsulate `at_page_beginning` and `at_page_end` usage via a context manager (`with ...`).


#### 2. Page marker methods

*   **`menu_page(*args, path: str | None = None, label: str | None = None, icon: str | None = None, **kwargs)`**

> Marker method for automagic menu builder. Used in `scan_menu_pages()` to build the application menu.

*   **`menu_item(id: str | None = None)`**

> Marker method for automagic menu assembler. Used in `assemble_menu_pages()` to fill the application menu map.

*   **`service_page()`**

> Marker method for registering Streamlit pages that should *not* appear in the navigation sidebar.


#### 3. Menu automagic and streamlit_page()

*   **`streamlit_page(menu_pages_tree: MenuTree, service_pages: list[st.Page], initial_page_title: str | None = None, menu_directory_item_icon: str = ":material/folder:") -> st.Page`**

> Registers all menu and service pages with Streamlit and renders a recursive sidebar using `st.expander()` and `st.page_link()`. `MenuTree` is `dict[str | None, MenuTree | st.Page]`
> Returns the current page selected by `st.navigation()`. You use this function in your Streamlit UI main file.

*   **`scan_menu_pages(ui_package_root: str | Path, *ui_package_path: str, mapper: Literal["sort", "token_underscore"] | Callable[[MenuTree], MenuTree] = "sort") -> MenuTree`**

> Scans all `.py` files for `menu_page()` calls and builds a sidebar menu tree (`MenuTree`).
> Supports natural sorting (`"sort"`) or token-based sorting (`"token_underscore"`).

*   **`assemble_menu_pages(skeleton: MenuSkeleton, ui_package_root: str | Path, *ui_package_path: str) -> MenuTree`**

> Scans `menu_item()` calls and assembles a recursive sidebar tree (`MenuTree`) based on a provided `MenuSkeleton`. 
> Raises `ValueError` for invalid configurations or unused scanned IDs.

*   **`scan_service_pages(ui_package_root: str | Path, *ui_package_path: str) -> list[st.Page]`**

> Scans all `.py` files for `service_page()` calls and returns a list of corresponding `st.Page` objects.

*   **`streamlit_main_sctipt_path() -> Path`**

> Returns the `Path` object pointing to the Streamlit main script path used with the `streamlit run` command.


### 3. User and its UserDataSource - UserService - CurrentUserService

> Provides a basic user management flow in `security.basic`.
>
> In `user`, defines the `User` class, serving as a Data Transfer Object (DTO) and record structure to hold user details, including roles, activity status, and service permissions.
>
> In `data_source`, defines abstract and concrete data source layers (`UserDataSource` and its basic implementation `LocalUserDataSource`) for performing CRUD operations on user records, utilizing SQLite for persistence in a simple implementation.
>
> In `user_service`, provides a comprehensive service layer (`UserService`) for handling user authentication, session management (both UI and token-based), and user data operations, enforcing security policies like login attempt limits and password requirements.
>
> In `current_user_service`, provides a `CurrentUserService` as a facade to encapsulate `UserService` logic for current user only.


#### 1. Domain class User

`quick_webapp.security.basic.user`

> In `user`, a record class representing a user, containing details like username, roles, activity flags (active, locked), and whether the user is intended for UI or service access.

- **`user_name: str`**

> Username or login. Returns the stripped version of the constructor `user_name` argument, or `None` if invalid.

- **`is_ui_user: bool`**

> Flag indicating if the user is allowed to log in via the UI.

- **`is_service_user: bool`**

> Flag indicating if the user is allowed to use services (APIs).

- **`name: str | None`**

> Common person name. Returns `None` if the constructor `name` argument was not a valid string.

- **`roles: list[str]`**

> A copy of the list of user roles assigned to the user.

- **`has_roles(roles: str | Sequence[str]) -> bool`**

> Checks if the user possesses any of the specified roles. Returns `True` if the role matches the user's roles (either as a single string or within a sequence).

- **`locked: bool`**

> Flag indicating if the user account is locked.

- **`active: bool`**

> Flag indicating if the user account is active.

- **`requires_password_update: bool`**

> Flag indicating if the user needs to set a new password.


#### 2. UserDataSource class and its basic implementation

`quick_webapp.security.basic.data_source`

> In `data_source`, the class is an interface, an abstract base class defining the contract for any user data source implementation.

- **`create_user(user: User, password: str, details: str)`**
> Creates a new user record using the provided `User` DTO, password, and details. Returns the created `User` object.

- **`is_user_exist(user_name: str)`**
> Checks whether a user with the given `user_name` exists in the data source.

- **`get_user_password(user_name: str)`**
> Fetches the password associated with the specified `user_name`.

- **`get_user_details(user_name: str)`**
> Fetches the detailed description associated with the specified `user_name`.

- **`get_user(user_name: str)`**
> Fetches and returns a complete `User` record based on the `user_name`.

- **`get_users(user_name_part: str, offset: int, limit: int, excluding_user_names: list[str] | None = None)`**
> Fetches a paginated list of users whose `user_name` contains `user_name_part`, optionally excluding specified users.

- **`update_user_lock(user_name: str, lock: bool)`**
> Updates the locked status of a specific user.

- **`update_user(user: User, details: str | None = None)`**
> Updates existing user information (name, roles, flags) and optionally the user details. Returns the updated `User` object.

- **`save_user(user: User, password: str, details: str | None = None)`**
> Saves/updates an existing user's information and password. Returns the saved `User` object.

- **`get_roles()`**
> Fetches a list containing all predefined user roles available in the system.


##### LocalUserDataSource class

> A concrete implementation of `UserDataSource` that uses an SQLite database (`users.db`) to store and manage user data.
> You might implement a custom UserDataSource and pass the instance into the UserService.
>
> Intended to be used for prototyping and simplicity.


#### 3. UserService class and its surroundings

`quick_webapp.security.basic.user_service`

>  In `user_service`, a service layer for handling user authentication, session management (both UI and token-based), and user data operations, enforcing security policies like login attempt limits and password requirements.
>
> `UserService` keeps all user-centric logic like sessions, login and authentication.
>
> Even though classes `Session` and `UserSession` are public, they are not emitted into outside world like `SessionsInfo` is.


##### 1. UserService class

> The primary service layer class responsible for all user-password based authorization, login management, and user data manipulation, requiring initialization with a `UserDataSource` and various validation/hashing functions.

- **`__init__(user_data_source: UserDataSource, password_hash_function: Callable[[str], str], password_hash_check_function: Callable[[str, str], bool], token_generator: Callable[[User, int], str], details_cipher_function: Callable[[str], str] = lambda plain_user_details: plain_user_details, details_decipher_function: Callable[[str], str] = lambda ciphered_user_details: ciphered_user_details, user_name_validator: Callable[[str], bool] = lambda user_name: True, password_validator: Callable[[str], bool] = lambda passsword: True, token_validator: Callable[[str], bool] = lambda token: True, max_login_attempts = 3, session_lifespan_seconds = 3600)`**

> Initializes the service with data source dependencies, password hashing/checking functions, token generation/validation functions, and operational constants like maximum login attempts and session lifespan.

- **`login(user_name: str, password: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> str`**

> Authenticates the user via username and password, checks credentials, and, if successful and allowed, sets a new session and returns a session ID.

- **`is_logged_in(session_id: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> bool`**

> Checks if a provided `session_id` corresponds to a currently valid and active user session based on client context.

- **`is_new_password_update_required(session_id: str) -> bool`**

> Checks if the user associated with the given `session_id` has the `requires_password_update` flag set.

- **`is_allowed(session_id: str, with_roles: str | list[str] | None = None) -> bool`**

> Checks if the user associated with the `session_id` possesses the specified roles (`with_roles`).

- **`set_password(session_id: str, password: str, new_password: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> str`**

> Allows the current user to set a new password. This action clears all existing sessions and returns a new session ID upon successful update.

- **`logout(session_id: str) -> None`**

> Invalidates and removes a specific user session from the service's cache.

- **`get_user(session_id: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> User`**

> Retrieves the full `User` record if the provided `session_id` is active and valid based on client context.

- **`get_user_details(session_id: str, user_locale: str, user_timezone: str, user_agent: str | None, ip_address: str | None) -> dict[str, Any]`**

> Retrieves and deserializes the user's detailed information if the provided `session_id` is active and valid.

- **`fetch_user(user_name: str) -> User`**

> Retrieves a `User` record directly by `user_name` from the data source, without requiring an active session.

- **`fetch_user_details(user_name: str) -> dict[str, Any]`**

> Retrieves and deserializes the user's detailed information directly by `user_name` from the data source.

- **`fetch_users(user_name_part: str, offset: int = 0, limit: int = 10, excluding_user_names: list[str] | str | None = None) -> list[User]`**

> Fetches a paginated list of users whose `user_name` matches the `user_name_part`.

- **`register_user(user: User, password: str, details: dict[str, Any] | None = None) -> User`**

> Creates a new user record in the data source, validating inputs before creation.

- **`update_user(user: User, password: str | None = None, details: dict[str, Any] | None = None) -> User`**

> Updates an existing user's information (name, roles, flags) and optionally their password or details, and closes all active sessions for that user.

- **`update_user_lock(user_name: str, lock: bool = True) -> None`**

> Updates the locked status of a specific user in the data source and closes all active sessions for that user.

- **`get_token(user_name: str, password: str) -> tuple[str, int]`**

> Authenticates a service user and generates a corresponding API token and its expiration timestamp.

- **`is_token_valid(token: str) -> bool`**

> Validates an API token, ensuring it is not expired and the associated user is active and not locked.

- **`is_token_allowed(token: str, with_roles: str | list[str] | None = None) -> bool`**

> Validates an API token and checks if the associated user possesses the specified roles.

- **`get_user_sessions_info(user_name: str) -> SessionsInfo | None`**

> Returns a `SessionsInfo` object detailing all currently active UI and token session intervals for a given user.

- **`get_all_sessions_info(user_name_part: str, offset: int = 0, limit: int = 10, excluding_user_names: list[str] | str | None = None) -> list[SessionsInfo]`**

> Retrieves a paginated list of `SessionsInfo` for users whose names match `user_name_part`.

- **`clear_all_expired_sessions() -> None`**

> Clears all expired UI and token sessions from the service's in-memory cache.

- **`close_all_sessions(user_name: str) -> None`**

> Invalidates and removes all UI and token sessions associated with a specific user, forcing re-authentication.

- **`max_login_attempts: int`**

> The maximum number of failed login attempts allowed before a user account is locked.

- **`session_lifespan_seconds: int`**

> The duration (in seconds) for which both UI and token sessions remain valid after creation.

- **`validate_user_name(user_name: str) -> bool`**

> Validates a username against the criteria defined during the service initialization.

- **`validate_password(password: str) -> bool`**

> Validates a password against the criteria defined during the service initialization.


##### 2. SessionsInfo class

> Record class that aggregates session lifespan information for a specific user, separating UI sessions from API token sessions.

- **`user: User`**

> The `User` record associated with this session information.

- **`user_sessions_lifespans: list[tuple[int, int]]`**

> A tuple listing the lifespan intervals (`int`, since-till POSIX timestamps) for the user's UI sessions.

- **`user_sessions_count: int`**

> The total count of the user's UI sessions.

- **`token_sessions_lifespans: list[tuple[int, int]]`**

> A tuple listing the lifespan intervals (`int`, since-till POSIX timestamps) for the user's token sessions.

- **`token_sessions_count: int`**

> The total count of the user's token sessions.


#### 4. The current User

`quick_webapp.security.basic.current_user_service`

> In `current_user_service`,  a facade for `UserService` that encapsulates default behavior for the currently logged-in user, simplifying page code by handling session retrieval and permission checks declaratively.


##### 1. CurrentUserService facade class

- **`__init__(user_service: UserService, login_page: str | Path, no_permision_page: str | Path, no_permision_query_key: str = "reload", no_permision_query_value: str = True, session_id_key = "session_id")`**

> Initializes the service with the core `UserService` and defines paths for the login and no-permission pages.

- **`get_user() -> User`**

> Fetches the currently logged-in user using session cookies.

- **`get_user_details() -> dict[str, Any]`**

> Fetches the current user's detailed information using session cookies.

- **`is_logged_in() -> bool`**

> Checks if the current user is logged in and their session is valid.

- **`is_new_password_update_required() -> bool`**

> Checks if the current user needs to update their password.

- **`is_allowed(with_roles: list[str] | str) -> bool`**

> Checks if the current user possesses the required roles.

- **`only_permitted(with_roles: list[str] | str = None)`**

> Checks login status, password update status, and required roles, redirecting to the login or no-permission page if checks fail.
>
> Also, acts as a marker method to collect permitted roles in `scan_pages_permissions()`

- **`logout() -> None`**

> Invalidates the current user session and redirects to the login page.


##### 2. Scan and filter permission

- **`scan_pages_permissions(ui_package_root: str | Path, *ui_package_path: str) -> dict[Path, list[str] | None]`**

> Scans all UI files for `only_permitted()` calls and returns a dictionary mapping page paths to the required roles (or `None` if no restriction).
>
> You use the result of this function with `filter_only_permitted_menu_pages()` and `filter_only_permitted_service_pages()` as a `permission_map` argument, ideally from the cached context.

- **`filter_only_permitted_menu_pages(menu_pages_tree: MenuTree, current_user_service: CurrentUserService, permission_map: dict[Path, list[str] | None]) -> MenuTree`**

> Filters the application menu tree, including only pages for which the current user is permitted, based on the `permission_map`.
> 
> You use the result of this function with `webapp.streamlit_page()` as a `menu_pages_tree` argument, ideally in the cached context.

- **`filter_only_permitted_service_pages(service_pages: list[st.Page], current_user_service: CurrentUserService, permission_map: dict[Path, list[str] | None]) -> list[st.Page]`**

> Filters the list of service pages, including only those accessible by the current user, based on the `permission_map`.
>
> You use the result of this function with `webapp.streamlit_page()` as a `service_pages` argument, ideally in the cached context.


### 4. Package `ui`

`quick_webapp.ui`

> This package contains UI related utilities and core functionalities UI implementations. 


#### 1. Package UI functions

> A collection of utility functions for interacting with the browser environment, cookies, and styling within a Streamlit application.
>
> Provides functions to execute JavaScript, manage HTTP cookies, fetch browser/network details, logging to console, restarting the script/browser, applying CSS, and generating unique CSS class names.

- **`execute_javascript(script: str)`**

> Executes a provided JavaScript string within a Streamlit element container, ensuring the script is hidden from display.

- **`write_cookie(key: str, value: str, max_age_seconds: int)`**

> Writes a real HTTP cookie into the parent browser window.

- **`read_cookie(key: str, alter: str | None = None)`**

> Reads the initial cookie from Streamlit's server context on the next rerun.

- **`delete_cookie(key: str)`**

> Deletes a real HTTP cookie from the parent browser window by setting max-age to 0.

- **`get_browser_locate() -> str`**

> Fetches the user browser's locale string from Streamlit context.

- **`get_browser_timezone() -> str`**

> Fetches the user browser's timezone string from Streamlit context.

- **`get_browser_user_agent() -> str | None`**

> Fetches the "user-agent" header from Streamlit context.

- **`get_ip_address() -> str | None`**

> Fetches the IP address of the user connection from Streamlit context.

- **`console_log(value: str)`**

> Adds JavaScript to the page to print a log message to the browser console.

- **`console_warning(value: str)`**

> Adds JavaScript to the page to print a warning log message to the browser console.

- **`console_error(value: str)`**

> Adds JavaScript to the page to print an error log message to the browser console.

- **`restart_script(delay_seconds: float = 0)`**

> Reruns the Streamlit script, optionally after a specified delay.

- **`restart_browser_window(delay_seconds: float = 0)`**

> Refreshes the browser window, optionally after a specified delay, using JavaScript `setTimeout`.

- **`apply_css(stylesheet: str)`**

> Adds a CSS style block directly to the Streamlit page using `st.html`.

- **`classname_streamlit(class_name: str, unique: bool = True)`**

> Returns a string pair for CSS use: the class name (potentially with a UUID suffix) and the corresponding Streamlit key (e.g., `.st-key-...`).


#### 2. DataView and PageContext util classes

`quick_webapp.ui.data_view`

`quick_webapp.ui.page_context`

> 	`DataView` is a utility class in `data_view` for structured data representation and UI parsing.
>
> `PageContext` is a utility class in `page_context` for managing page-related data and application state in Streamlit .

##### 1. DataView class

> Represents a data view suitable for convenient parsing in the UI, containing a label, rows, and nested sections.

- **`constructor(label: str, original: Any = None)`**

> Initializes the structure with a label and an original object from which this data view was parsed.

- **`add_row(row: dict[str, Any])`**

> Adds a single row (dictionary) to the data view's collection of rows.

- **`add_section(section: DataView)`**

> Adds a nested subsection (`DataView` instance) to the current data view.

- **`label: str`**

> Returns the title or label of the data view.

- **`has_label: bool`**

> Checks if the data view has a non-empty label.

- **`rows: list[dict[str, Any]]`**

> Returns the list of rows contained in the data view.

- **`rows_length: int`**

> Returns the total count of rows in the data view.

- **`sections: list[DataView]`**

> Returns the list of nested subsections (`DataView` instances).

- **`sections_length: int`**

> Returns the total count of subsections in the data view.

- **`original`**

> Returns the original data object associated with this view, if provided during initialization.

- **`has_original`**

> Checks if there is an original data object associated with this view.


##### 2. PageContext class

> Simple helper class to hold page related data and state, providing shortcuts for working with state dictionaries.
>
> Perfectly, you use this class from a factory fuction decorated with `@session_bean`

- **`constructor(key: str, contexts: dict[str, dict[Any, Any]] | None = None, default_context: dict[Any, Any] | None = None, notification_duration_seconds: int = 2)`**

> Initializes the context with a unique key, optional context dictionaries, a default context, and the duration for showing notifications in seconds.

- **`key: str`**

> Returns the unique data key associated with this page context.

- **`make_subkey(suffix: str) -> str`**

> Creates a unique key by appending a suffix to the main page key (e.g., `page_key_suffix`).

- **`get_context(name: str | None = None) -> dict[Any, Any]`**

> Retrieves a specific context dictionary by its name, or returns the default context if the name is not found.

- **`put_notification(message: str, message_icon: str | None = None, pre_notification_action: Callable[[PageContext], Any] | None = None, post_notification_action: Callable[[PageContext], Any] | None = None)`**

> Registers a notification message along with optional pre- and post-actions to be executed when the notification is fired.

- **`fire_notifications(rerun_scope: str | None = None)`**

> Processes and displays all registered notifications using `st.toast()`. Optionally performs a Streamlit rerun after firing all notifications.

- **`apply(action: Callable[[PageContext], Any], rerun_scope: str | None = None)`**

> Executes a provided action function against this `PageContext`. Optionally performs a Streamlit rerun after the action is completed.


#### 2. Basic rendering

`quick_webapp.ui.render`

> Provides functions to display objects (including `DataView`, mappings, and `DataFrames`), manage reactive UI fragments, render exception messages, and visualize git-like text diffs.

- **`render(obj: Any, label: str | None = None)`**

> Renders a given object in a pretty-formatted way to Streamlit. Supports boolean, numeric, string, `DataView` (with nested sections and rows), `Mapping` (JSON), `Sequence` of mappings (table), and `DataFrame`.

- **`render_branched_fragment(predicate: bool, fragment_of_true: Callable[[], None], fragment_of_false: Callable[[], None], interval: float = 1.0)`**

> Renders a reactive UI element (`fragment_of_true` or `fragment_of_false`) based on a boolean predicate. If the predicate is false, it pauses execution for a specified interval and triggers a Streamlit rerun.

- **`render_exception_messages(e: BaseException, starter_message: str | None = None)`**

> Renders the primary exception message and all subsequent caused exception messages in a Streamlit error block.

- **`render_text_diff(old_text: str, new_text: str, line_numbers: bool = False, context_lines: int | None = 3, unchanged_lines_next: str = "unchanged lines omitted")`**

> Renders a git-like text diff view between two strings, supporting optional line numbers and a configurable number of context lines around changes.


#### 3. An action table

`quick_webapp.ui.action_table`

> Renders data in a customized table format where each data element is displayed using specific mappers, and corresponding actions (buttons or menu items) are available for each row.

- **`action_table(data: Iterable[Any], no_data_message: str, data_mappers: dict[str, Callable[[Any], None]], action_mappers: dict[str, Callable[[Any], None]], actions_col_label: str = None, action_button_type: str = None, action_menu_label: str = None, table_head_line_color: str = "silver", container_border: bool = True, container_width: str | int = "stretch", column_ratio_spec: list[int] = None, column_gap: str = "xxsmall", column_vertical_alignment: str = "center", key_suffix: str = "")`**

> Renders data as an action table. On the left, it renders data elements using `data_mappers`; on the right, it displays action controls (buttons or a menu) using `action_mappers`. The function handles layout, column ratios, styling, and displays a message if no data is provided.


#### 4. Editors and their data

`quick_webapp.ui.editor`

> An editor library providing an internal tree structure for editable data (dict/list) and a  code editor for code validation within Streamlit.
>
> To support this, implements `Node` structure for recursive data editing and a `CodeEditorValidationMessage` class to manage syntax/validation feedback for code input via `st_ace`.


##### 1. Data structure editors

> Functions and util Node class to edit structures and/or their data.


###### 1. Node class

> Internal representation of a node within an editable data tree. Uses a UUID for stable Streamlit widget keys, independent of its position in the data structure.
>
> You use this class directly only to provide its instance to the `structure_editor()` and `data_editor()` if needed, and it is a return object from the editors to call `data()` method. 
>
> Only methods that recommended for usage are covered.

- **`create(data: Any, parent: Node | None = None) -> Node`**

> Converts ordinary Python data (dict, list, or scalar) into an internal `Node` structure.

- **`data()`**

> Recursively converts the internal tree structure back into standard Python data (dict/list/scalar), respecting the `included` flag.


###### 2. Structure editor

- **`structure_editor(data: dict | list | Node, key: str, context: dict[str, Any], width: Literal["stretch", "content"] | int = "stretch", expander_help: str | None = None, expand_all_help: str | None = None, collapse_all_help: str | None = None, include_help: str | None = None, field_empty_error_text: str = "Field name is empty", field_exists_error_text: str = "Field name already exists", add_string_menu_text: str = "Add a string", add_int_menu_text: str = "Add an integer number", add_float_menu_text: str = "Add a floating number", add_bool_menu_text: str = "Add a boolean", add_null_menu_text: str = "Add null", add_object_menu_text: str = "Add an object", add_array_menu_text: str = "Add an array", clone_menu_text: str = "Clone", delete_menu_text: str = "Delete the field") -> Node`**

> Renders an editable tree view for a Python dictionary or list using Streamlit fragments. It manages the internal structure and state in the provided context dictionary.


###### 3. Data editor

- **`data_editor(data: dict | list | Node, key: str, context: dict[str, Any], expanded: bool | None = None, width: Literal["stretch", "content"] | int = "stretch", expand_all_label: str | None = None, collapse_all_label: str | None = None, is_one_based_array_index: bool | None = None) -> Node`**

> Provides a read-only editor version of the structure editor. Users can only edit the values of the data structure but not its schema (structure or data types).


##### 2. Code editor

> Code editor funtion and util CodeEditorValidationMessage class to pass to the editor on validation error.


###### 1. CodeEditorValidationMessage class

> Data structure to hold specific location information (row/column) and type (error, warning, info) for a validation message related to code editing. Appropriate view then will be rendered in the editor.
>
> You use this class a part of Callable that validates the current code string and returns an iterable of instances of this class.

 **`constructor(text: str, row: int, column: int, type: Literal["error", "warning", "info"] = "error")`**
 
> Initializes the message with text and 1-based row/column coordinates, defaulting the type to "error".

- **`row: int`**

> Returns the zero-based row index of the message.

- **`column: int`**

> Returns the zero-based column index of the message.

- **`text: str`**

> Returns the validation message string.

- **`type: str`**

> Returns the message type ("error", "warning", or "info").

- **`to_dict() -> dict[str, Any]`**

> Converts the validation message into a dictionary suitable for Streamlit Ace annotation.


###### 2. The editor

> A `streamlit_ace` wrapped code editor.

- **`code_editor(value: str, language: str, key: str, context: dict[str, Any], validator: Callable[[str], Iterable[CodeEditorValidationMessage]] | None = None, spaces_per_tab: int = 4, keybinding: str = "vscode", theme: str | None = None) -> str | None`**

> Renders a code editor using `streamlit_ace`. It automatically detects a suitable theme based on Streamlit configuration and uses a provided validator to display annotations/validation messages, returning `None` if any validation errors exist.

**Languages:** 

```
abap, abc, actionscript, ada, alda, apache_conf, apex, applescript, aql, asciidoc, asl, assembly_x86, autohotkey, batchfile, c9search, c_cpp, cirru, clojure, cobol, coffee, coldfusion, crystal, csharp, csound_document, csound_orchestra, csound_score, csp, css, curly, d, dart, diff, django, dockerfile, dot, drools, edifact, eiffel, ejs, elixir, elm, erlang, forth, fortran, fsharp, fsl, ftl, gcode, gherkin, gitignore, glsl, gobstones, golang, graphqlschema, groovy, haml, handlebars, haskell, haskell_cabal, haxe, hjson, html, html_elixir, html_ruby, ini, io, jack, jade, java, javascript, json, json5, jsoniq, jsp, jssm, jsx, julia, kotlin, latex, less, liquid, lisp, livescript, logiql, logtalk, lsl, lua, luapage, lucene, makefile, markdown, mask, matlab, maze, mediawiki, mel, mixal, mushcode, mysql, nginx, nim, nix, nsis, nunjucks, objectivec, ocaml, pascal, perl, perl6, pgsql, php, php_laravel_blade, pig, plain_text, powershell, praat, prisma, prolog, properties, protobuf, puppet, python, qml, r, razor, rdoc, red, redshift, rhtml, rst, ruby, rust, sass, scad, scala, scheme, scss, sh, sjs, slim, smarty, snippets, soy_template, space, sparql, sql, sqlserver, stylus, svg, swift, tcl, terraform, tex, text, textile, toml, tsx, turtle, twig, typescript, vala, vbscript, velocity, verilog, vhdl, visualforce, wollok, xml, xquery, yaml
```

**Keybinding:** 

```
emacs, sublime, vim, vscode
```

**Theme:** 

```
ambiance, chaos, chrome, clouds, clouds_midnight, cobalt, crimson_editor, dawn, dracula, dreamweaver, eclipse, github, gob, gruvbox, idle_fingers, iplastic, katzenmilch, kr_theme, kuroir, merbivore, merbivore_soft, mono_industrial, monokai, nord_dark, pastel_on_dark, solarized_dark, solarized_light, sqlserver, terminal, textmate, tomorrow, tomorrow_night, tomorrow_night_blue, tomorrow_night_bright, tomorrow_night_eighties, twilight, vibrant_ink, xcode
```


#### 5. User login, register and edit forms

`quick_webapp.ui.security.basic.form`

> Provides functions to display login, registration, password setting, creating, and editing user profiles, managing session state via browser cookies and Streamlit dialogs.

- **`login_form(user_service: UserService, session_id_key: str, registration_key: str | None, title: str, user_name_label: str, password_label: str, login_button_label: str, registration_button_label: str, help_text: str | None, help_badge: str, exception_text_mapper: Callable[[Exception], str])`**

> Displays a login dialog, handling user input, service login via `UserService`, and setting/deleting browser cookies for session and registration state.

- **`registration_form(user_service: UserService, default_roles: str | Iterable[str] | None, default_active_status: bool, registration_default_user_details_supplier: Callable[[], dict[str, Any]] | None, registration_key: str, title: str, user_name_label: str, full_name_label: str | None, password_label: str, confirm_password_label: str, register_button_label: str, login_button_label: str, help_badge: str, help_text: str | None, exception_text_mapper: Callable[[Exception], str], passwords_do_not_match_text: str)`**

> Displays a user registration dialog, collecting necessary user details (username, full name, password), registering the user via `UserService`, and managing registration state via browser cookies.

- **`set_password_form(user_service: UserService, session_id_key: str, title: str, password_label: str, new_password_label: str, confirm_new_password_label: str, set_button_label: str, exception_text_mapper: Callable[[Exception], str], passwords_do_not_match_text: str)`**

> Displays a dialog allowing a currently logged-in user to change their password, updating the session ID cookie upon success and handling session invalidation upon failure.

- **`create_user_form(user_service: UserService, registration_default_user_details_supplier: Callable[[], dict[str, Any]] | None, context: dict[str, Any], title: str, user_name_label: str, full_name_label: str | None, password_label: str, confirm_password_label: str, roles_label: str, is_ui_user_label: str, is_service_user_label: str, is_active_label: str, is_locked_label: str, is_password_set_required_label: str, details_label: str, create_button_label: str, exception_text_mapper: Callable[[Exception], str], passwords_do_not_match_text: str, key_suffix: str | None)`**

> Displays a form to create a new user, including options for UI/service user roles, status flags, and nested data editing via `data_editor()`.

- **`edit_user_form(user_name: str, user_service: UserService, context: dict[str, Any], title: str, full_name_label: str | None, password_label: str, confirm_password_label: str, roles_label: str, is_ui_user_label: str, is_service_user_label: str, is_active_label: str, is_locked_label: str, is_password_set_required_label: str, details_label: str, save_button_label: str, exception_text_mapper: Callable[[Exception], str], passwords_do_not_match_text: str, key_suffix: str | None)`**

> Displays a form to edit an existing user's details, fetching current user data via `UserService` and providing an editable tree view for complex attributes.


#### 6. Basic user login and management pages

`quick_webapp.ui.security.basic.page`

> Provides configuration structures and fragmented UI rendering functions for login, registration, password setting, user creation, user editing, and management of all users and current active user sessions.
>
> You use this functions on the appropriate login and user management pages.


##### 1. SecurityUIConfig class

> A record class that centralizes all user-facing UI configurations, including titles, labels, button texts, and shared messaging for all security-related forms and management pages.

- **`constructor(login_title: str = "Login", user_name_label: str = "Username", password_label: str = "Password", login_button_label: str = "Login", registration_button_label: str = "Registration", login_help_text: str | None = None, registration_title: str = "Registration", full_name_label: str | None = "Full name", confirm_password_label: str = "Confirm password", register_button_label: str = "Register", registration_login_button_label: str = "Login", registration_help_text: str | None = None, set_password_title: str = "Set a password", new_password_label: str = "New password", confirm_new_password_label: str = "Confirm new password", set_password_button_label: str = "Set", create_user_title: str = "Create a user", is_ui_user_label: str = "UI user", is_service_user_label: str = "Service user", roles_label: str = "Roles", is_active_label: str = "Active", is_locked_label: str = "Locked", is_password_set_required_label: str = "Require password set", create_user_button_label: str = "Create", edit_user_title: str = "Edit a user", save_button_label: str = "Save", clear_all_expired_sessions_label: str = "Clear expired", create_new_user_button_label: str = "New user", search_by_user_name_text_field_label: str = "User name:", search_by_user_name_button: str = "Search", user_name_column_label: str = "username", name_column_label: str = "Name", is_ui_user_column_label: str = "Regular user?", is_service_user_column_label: str = "Service user?", roles_column_label: str = "Roles", locked_column_label: str = "Is locked?", active_column_label: str = "Is active?", requires_password_update_column_label: str = "Must set password?", sessions_column_label: str = "Sessions", token_sessions_column_label: str = "Token sessions", logout_user_button_label: str = "Logout", edit_user_button_label: str = "Edit", no_users_found: str = "No users were found...", next_page_button_label: str = "Next >", back_page_button_label: str = "< Back", details_label: str = "Details", help_badge: str = "🛟", exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception), passwords_do_not_match_text: str = "Passwords do not match!", true_label: str = "✅", false_label: str = "⬜", null_text: str = "Not set", badge_background_color: str = "#6569C3", badge_foreground_color: str = "#ffffff")`**

> Initializes the configuration with default labels and texts for all authentication and user management UI components.


##### 2. Render pages

- **`render_login_page(user_service: UserService, session_id_key: str, logged_in_page_path: str | Path | st.Page, registration_key: str | None = None, registration_default_roles: str | Iterable[str] | None = None, registration_default_active_status: bool | None = None, registration_default_user_details_supplier: Callable[[], dict[str, Any]] | None = None, security_ui_config: SecurityUIConfig = SecurityUIConfig())`**

> Renders the initial login page. It checks for a valid session; if none exists, it displays the login or registration form, and redirects to `logged_in_page_path` upon successful login.

- **`render_all_users_management_page(user_service: UserService, registration_default_user_details_supplier: Callable[[], dict[str, Any]] | None, context: dict[str, Any], users_per_page = 10, excluding_user_names: list[str] | str | None = None, security_ui_config: SecurityUIConfig = SecurityUIConfig(), width: int | Literal["stretch", "content"] = "stretch", key: str | None = None, user_name_column_x = 1, name_column_x = 1.5, is_ui_user_column_x = 0.5, is_service_user_column_x = 0.5, roles_column_x = 2.5, active_column_x = 0.5, locked_column_x = 0.5, password_set_required_column_x = 0.5, edit_button_column_x = 0.5)`**

> Renders a page for managing all registered users, supporting search, pagination, and actions like creating a new user or editing an existing one.

- **`render_current_users_management_page(user_service: UserService, context: dict[str, Any], users_per_page = 10, excluding_user_names: list[str] | str | None = None, security_ui_config: SecurityUIConfig = SecurityUIConfig(), width: int | Literal["stretch", "content"] = "stretch", key: str | None = None, user_name_column_x = 1, name_column_x = 1.5, is_ui_user_column_x = 0.5, is_service_user_column_x = 0.5, roles_column_x = 2.5, sessions_column_x = 0.7, token_sessions_column_x = 0.7, buttons_column_x = 1)`**

> Renders a page listing all active sessions for the currently logged-in user, allowing for actions such as logging out a session or clearing all expired sessions.


### 5. Utilities

`quick_webapp.util`

> Provides optional useful function and classes.


#### 1. Commons

`quick_webapp.util.commons`

> Provides tools to include data from source dictionaries, locate files recursively, load `.env` files, and flatten complex exception chains into readable messages.

- **`include_value(key: str, source: dict[str, Any], mapping_key: str, target: dict[str, Any], value_mapper: None | Callable[[Any], Any] = None)`**

> Includes a value from a source dictionary into a target dictionary under a specified mapping key, only if the value is not None, optionally transforming the value using a provided mapper.

- **`get_file_paths(root: str | Path | None, extension: str | None, *path_nodes: str)`**

> Returns a sorted list of `Path` objects for all files matching a specified extension within a given root directory and path nodes. If no root is provided, it searches from the caller's parent directory.

- **`get_environment(path: str | None = ".env", push_to_env: bool | None = None)`**

> Loads environment variables from the specified `.env` file. Optionally pushes these variables into the system's `os.environ`.

- **`extract_exception_messages(exception: BaseException, starter_message: str | None = None)`**

> Recursively extracts all exception messages from a complex exception chain (including `__cause__` and `__context__`) and returns them as a list of strings, optionally prefixed by a starting message.


#### 2. Network

`quick_webapp.util.network`

> Provides simple methods to test if a server is reachable via a raw TCP connection or via a standard HTTP request.

- **`tcp_ping(url, port=443, timeout=5)`**

> Checks if the server specified by the URL is available by attempting a TCP connection to the given port within a specified timeout. Returns `True` if successful, `False` otherwise.

- **`http_ping(url: str, method: str = "HEAD", timeout: int = 5) -> Optional[int]`**

> Checks if the server is available for HTTP requests using a specified method (defaults to HEAD). Returns the HTTP status code upon success, or `None` if a request exception occurs.


#### 3. Reflection

`quick_webapp.util.reflection`

> Implements a function to scan Python source files within a package and extract all calls to a specified function name, including positional arguments and keyword arguments.

- **`scan_params(function_name: str, package_root: str | Path | None, *package_path: str) -> dict[Path, list[dict[str, Any]]]`**

> Scans all `.py` files within a given package root (and optional subpaths) for calls to `function_name`. Returns a dictionary where the key is the file path and the value is a list of dictionaries, each containing the list of positional arguments (`args`) and the dictionary of named keyword arguments (`kwargs`) for that call.
>
> Used under the hood in `scan_menu_pages()`, `assemble_menu_pages()`, `scan_service_pages()` and `scan_pages_permissions()`


#### 4. ShutdownHookHolder class

`quick_webapp.util.shutdown_hook`

> Wrapper structure designed to hold and execute a list of actions (callables) during application shutdown.

- **`constructor(hook_logger_name: str)`**

> Initializes the hook holder, sets up an internal list for actions, configures a logger, and registers the `terminate` method with `atexit`.

- **`add_hook(callable: Callable[[], Any])`**

> Registers a callable function to be executed when the application shuts down.

- **`terminate()`**

> Executes all registered cleanup actions in LIFO order, catching and logging any exceptions that occur during the execution of these hooks.


#### 5. TemporaryStorage class

`quick_webapp.util.temporary_storage`

> Stores and retrieves binary data using unique IDs within a `.temp` directory, providing methods for writing, reading (as stream or bytes), and safely cleaning up temporary files and the internal registry.

- **`constructor()`**

> Initializes the storage by ensuring the `.temp` directory exists and setting up an internal registry mapping friendly names to file UUIDs.

- **`contains_binary(name: str)`**

> Checks if a temporary file associated with the given name exists and is a file, returning `False` if the name is not in the registry.

- **`write_binary(name: str, binary: bytes | io.BytesIO)`**

> Stores binary data (either raw bytes or a `io.BytesIO` stream) in the temporary storage and registers the file by the given name.

- **`read_binary_as_stream(name: str)`**

> Reads the binary data from temporary storage and returns it as an `io.BytesIO` stream. Raises `FileNotFoundError` if the name is not found.

- **`read_binary_as_bytes(name: str)`**

> Reads the binary data from temporary storage and returns it as a standard `bytes` object. Raises `FileNotFoundError` if the name is not found.

- **`delete_binary(name: str)`**

> Deletes the temporary file associated with the given name from the disk and removes the entry from the internal registry.

- **`delete_all()`**

> Removes the entire `.temp` directory and clears the internal registry, cleaning up all temporary files.


#### 6. TaskManager class

`quick_webapp.util.task_manager`

> Provides methods to schedule a callable function for execution, supporting configurable retry attempts and sleep intervals between attempts, along with standard task management functions (checking completion, retrieving results, and cancellation).
>
> Wrapper around an ExecutorService that manages tasks, including a task counter and built-in retry logic for scheduled callables.

- **`constructor(thread_name_prefix)`**

> Initializes the task manager by setting up a thread-safe lock, an internal task registry, and a `ThreadPoolExecutor` with a specified thread name prefix.

- **`schedule(callable_: Callable[[], Any], attempts: int = 1, sleep_interval: float = 1.0) -> int`**

> Schedules a callable function for asynchronous execution. The task will retry up to `attempts` times with a delay of `sleep_interval` seconds between failures, stopping when the callable returns a non-None value or attempts are exhausted.
>
> Returns a unique task ID.

- **`is_completed(task_id: int) -> bool`**

> Checks whether the asynchronous task identified by `task_id` has finished execution.

- **`result(task_id: int) -> Any`**

> Retrieves the final result of a completed task, or re-raises any exception that occurred during execution.

- **`cancel(task_id: int) -> bool`**

> Attempts to cancel the running task associated with `task_id`, returning `True` if cancellation was successful.

- **`throw_away(task_id: int)`**

> Removes a task from the task registry. If the task is still running, it attempts to cancel it before removal.

- **`shutdown_now()`**

> Initiates a non-blocking shutdown of the internal thread pool executor and cancels all remaining unfinished tasks.


#### 7. LLM clients

`quick_webapp.util.llm`

> Defines data structures (`Content`, `Message`, `JsonSchema`, `Chat`) for chat history and provides abstract (`LLMClient`) and concrete (`OpenAICompatibleClient`, `OpenAIClient`) classes for interacting with LLM APIs, supporting streaming and generation interruption.

##### 1. Data classes 


###### 1. Content class

> Data class representing a single piece of chat content, which must be either "text" or "image".

- **`constructor(type: str, content: str)`**

> Initializes content, ensuring the type is valid ("text" or "image") and the content string is non-empty.

- **`type: str`**

> Returns the content type ("text" or "image").

- **`content: str`**

> Returns the raw string content of the message.


###### 2. Message class

> Data class representing a single chat message, which can contain one or more `Content` elements and optional reasoning content.

- **`constructor(role: str, content: Content | list[Content], reasoning_content: str | None = None)`**

> Initializes the message, ensuring the role is valid ("user" or "assistant") and content is a single `Content` object or a list of them.

- **`role: str`**

> Returns the message role ("user" or "assistant").

- **`content: Iterator[Content]`**

> Returns an iterator over the message's `Content` elements.

- **`first_content(): Content`**
> Returns the first `Content` element in the message.

- **`reasoning_content: str`**

> Returns the optional reasoning content associated with the message.

- **`has_reasoning_content() -> bool`**

> Checks if reasoning content was provided for the message.


###### 3. JsonSchema class

> Helper class to build a JSON schema definition based on a base example, ensuring it is suitable for guiding structured LLM output.

- **`constructor(name: str, base_example: dict[str, Any], top_level_required_fields: list[str] | str | None = None)`**

> Initializes the schema by building an object schema from a base example, setting the type to "object" and enforcing `additionalProperties` to `False`.

- **`name: str`**

> Returns the name of the JSON schema.

- **`schema: dict[str, Any]`**

> Returns the complete JSON schema dictionary.


###### 4. Chat class

> Data class representing a conversational chat session, holding a system prompt, reasoning display preference, and a history of `Message` objects.

- **`constructor(system_prompt: str | None = None, show_reasoning: bool = True, json_schema: JsonSchema | None = None)`**

> Initializes the chat with an optional system prompt, reasoning display setting, and a JSON schema constraint.

- **`system_prompt: str`**

> Returns the system instruction prompt for the LLM.

- **`show_reasoning: bool`**

> Returns the setting indicating whether reasoning should be displayed.

- **`json_schema: JsonSchema | None`**

> Returns the configured JSON schema object, if applicable.

- **`messages: Iterator[Message]`**

> Returns an iterator over the sequence of chat messages in the session.

- **`has_messages(): bool`**

> Checks if the chat session contains any messages.

- **`add_message(message: Message)`**

> Appends a new message to the chat history.

- **`interrupted: bool`**

> Boolean flag indicating if the last message generation was interrupted.


##### 5. Clients


###### 1. Base LLMClient class

> Abstract base class defining the required interface for any OpenAI-compatible LLM client.

- **`constructor()`**

> Initializes internal dictionaries to manage active chats (`__chats`) and stateless chats (`__chatless`).

- **`create_chat(system_prompt: str | None = None, show_reasoning: bool = True, json_schema: JsonSchema | None = None) -> int`**

> Initializes a new chat session, storing the configuration and returning a unique chat ID.

- **`prompt(content: Any | list[Any], chat_id: int | None = None) -> Iterator[str]`**

> Sends content (string or list) to the LLM, optionally within a specific chat session. Returns a streaming iterator of line strings containing tokens (reasoning and final response).

- **`prompt_and_wait(content: Any | list[Any], chat_id: int | None = None) -> str`**

> Wraps `prompt()` to consume the entire streaming response and returns the complete, concatenated response string.

- **`interrupt(chat_id: int | None = None)`**

> Interrupts the ongoing LLM response generation, either for a specific `chat_id` or across all current sessions.

- **`get_messages(chat_id: int) Iterator[Message]`**

> Returns an iterator of all `Message` objects stored in a specific chat session.

- **`delete_chat(chat_id: int = None)`**

> Deletes a specific chat session by ID, or deletes all stateless chats if no ID is provided.

- **`support_images() -> bool`**

> Abstract method to check if the LLM supports image input (vision).

- **`ping() -> bool`**

> Abstract method to check the availability of the LLM endpoint.


###### 2. Local and cloud LLMClients

 1. **OpenAICompatibleClient class**

> Concrete LLM client implementation compatible with a generic API endpoint, supporting images and structured JSON output.

- **`constructor(api_key: str, host: str, port: int | None = None)`**

> Initializes the client by setting up the API URL, storing the API key, and maintaining a request ID map.


2. **OpenAIClient class**

> Concrete LLM client implementation specifically tailored for the standard OpenAI API endpoint.

- **`constructor(model: str, api_key: str)`**

> Initializes the client with a specific model name and the OpenAI API key, setting the base URL.
