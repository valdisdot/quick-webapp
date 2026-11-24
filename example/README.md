## quick_webapp Example

> This file demonstrates a fully functional, multi-page application using the `quick_webapp` framework. 
> 
> It showcases core features such as global/session state management, secure routing, dynamic menu building, and advanced UI components like the Action Table.


### File Structure

```
example/
  context.py       # Application configuration and bean definitions (Singleton/Session)
  main.py          # Streamlit entry point
  page/
    action_table.py          # Demonstrates Action Table UI
    admin_page.py            # Demonstrates Admin-level security
    extended_menu_page.py    # Demonstrates dynamic page switching
    home.py                  # Home page with user greeting
    login.py                 # Authentication entry point
    simple_page.py           # Demonstrates session-scoped state
    user_management/
      all_users.py          # All user management (Search/Pagination)
      current_users.py      # Current user session monitoring
```


### Application Initialization (`context.py` & `main.py`)

> `context.py` serves as the application's configuration layer.

*   **Global Singletons (`@bean`):** `webapp()`, `user_data_source()`, and `user_service()` are registered globally, ensuring they are initialized only once across the entire application lifetime.

*   **Session State (`@session_bean`):** `user_menu_pages()` and `user_service_pages()` are session-scoped, guaranteeing that permissions and menu trees are specific to the currently logged-in user.

*   **Navigation Setup:** `menu_pages()` scans all files using `scan_menu_pages()`. This tree is then filtered by `filter_only_permitted_menu_pages()` using the `CurrentUserService`'s permission checks.


**`main.py` (Entry Point):**

```python
from quick_webapp.webapp import streamlit_page
from context import user_menu_pages, user_service_pages

# Passes the *filtered* menu and service pages to the core Streamlit runner
streamlit_page = streamlit_page(
    user_menu_pages(),
    user_service_pages(),
    "Welcome to example!"
)
streamlit_page.run()
```

### Security and Access Control (`login.py`, `admin_page.py`)

> The framework handles authentication and permission checks declaratively.

*   **Login Flow (`login.py`):** Uses `service_page()` and `user_service` to manage session cookies (`read_cookie`), validate sessions (`is_logged_in`), and display standard forms (`login_form`).

*   **Role Enforcement:** `admin_page.py` enforces role access:

    ```python
    # admin_page.py
    current_user_service = current_user_service()
    # If user is not an 'admin', they are automatically redirected/blocked
    current_user_service.only_permitted("admin") 
    ```

    *Reference: `README.md` Section 3.4.*


### State Management and UI Context (`simple_page.py`, `action_table.py`)

*   **Session State:** `simple_page.py` uses `@session_bean` (`__context`) to store user input (`last_text`) which persists across Streamlit reruns within the same session.

    *Reference: `README.md` Section 1.1.*

*   **Page Context:** `action_table.py` uses `PageContext` (via `@session_bean`) to encapsulate transient page data (e.g., the `orders` list) and manage notifications (`put_notification`, `fire_notifications`).

    *Reference: `README.md` Section 4.2.*

*   **Web Context:** Every page utilizes `with webapp().as_context(...)` to consistently apply the custom header and shared styles.

    *Reference: `README.md` Section 2.2.*


### Advanced UI Components


#### Action Table (`action_table.py`)

> This demonstrates how to combine structured data with row-level actions using `action_table()`.

```python
# action_table.py excerpt
action_table(
        data=__page_context().get_context()["orders"],
        no_data_message="No orders...",
        data_mappers=__data_mappers(),  # Defines how data fields are rendered (e.g., "Title": lambda o: st.write(o.title))
        action_mappers=__action_mappers(), # Defines row actions (e.g., "Edit": lambda order: __edit(order, page_context))
        column_ratio_spec=[6, 2, 2, 1, 1], # Custom layout control
        container_width=1000
)
```

*Reference: `README.md` Section 4.3.*


#### User Management (`user_management/all_users.py`)

This page demonstrates complex application state within the session context for data presentation:

1.  Search input and button trigger a state update (`page_context["q_user_name"] = q_user_name`).
2.  The service (`user_service.fetch_users`) is called based on this state.
3.  Pagination logic (checking `has_next`/`has_previous`) manages `offset` state within `page_context`.
4.  The data and actions are rendered via `action_table`.


### Key Takeaways

| Concept | Usage Example | Benefit |
| :--- | :--- | :--- |
| **`@bean`** | `user_service()` | Global, shared resource (Singleton) across all users. |
| **`@session_bean`** | `__page_context()` | Isolated state, ensuring user data (e.g., form inputs, notifications) doesn't bleed between sessions. |
| **`only_permitted()`** | `current_user_service.only_permitted("admin")` | Declarative security; prevents unauthorized page access before UI rendering. |
| **`menu_page()`** | `menu_page("9_User Management", "1_All")` | Automated sidebar generation via scanning, requiring minimal boilerplate code. |
| **`action_table()`** | `action_table(...)` | Powerful, customized UI for displaying data alongside interactive, row-specific actions. |