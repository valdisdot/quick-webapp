import time
from uuid import uuid4
import streamlit as st

def execute_javascript(script: str):
    wrapped_script = f"""
    <div class="js-executor">
        <script>
            (function() {{
                const currentScript = document.currentScript;
                const container = currentScript.closest(
                    '[data-testid="stElementContainer"]'
                );

                if (container) {{
                    container.style.display = 'none';
                }}

                {script}
            }})();
        </script>
    </div>
    """

    st.html(
        wrapped_script,
        width="content",
        unsafe_allow_javascript=True
    )

def write_cookie(key: str, value: str, max_age_seconds: int):
    """
    Writes a real HTTP cookie into the parent browser window.
    """
    
    execute_javascript(f'window.parent.document.cookie = "{key}={value}; max-age={max_age_seconds}; path=/;";')

def read_cookie(key: str, alter: str | None = None) -> str | None:
    """
    Reads the initial cookie on the next rerun from the server side. 
    The browser refreshing must be called if the application writes cookies in runtime and need to fetch them back.
    """
    return st.context.cookies.get(key, alter)

def delete_cookie(key: str) -> str | None:
    """
    Deletes a real HTTP cookie from the parent browser window.
    The browser refreshing must be called if the application deletes cookies in runtime and need to ensure they are deleted in streamlit cookies.
    """

    execute_javascript(f'window.parent.document.cookie = "{key}=; max-age=0; path=/;";')

def get_browser_locate() -> str:
    """
    Fetches user browser's locale string.
    """

    return st.context.locale

def get_browser_timezone() -> str:
    """
    Fetches user browser's timezone string.
    """
    return st.context.timezone

def console_log(value: str):
    """
    Adds JavaScript to the page to print a log message to the browser console.
    """

    execute_javascript(f"console.log('{str(value)}');")

def console_warning(value: str):
    """
    Adds JavaScript to the page to print a warning log message to the browser console.
    """

    execute_javascript(f"console.warn('{str(value)}');")

def console_error(value: str):
    """
    Adds JavaScript to the page to print an error log message to the browser console.
    """

    execute_javascript(f"console.error('{str(value)}');")

def restart_script(delay_seconds: float = 0):
    """
    Reruns Streamlit script with delay.
    """

    if delay_seconds > 0:
        time.sleep(delay_seconds)

    st.rerun()

def restart_browser_window(delay_seconds: float = 0):
    """
    Refreshes browser window with delay.
    """
        
    delay_ms = max(0, int(delay_seconds * 1000))

    execute_javascript(f"""
        setTimeout(() => {{
            window.parent.location.reload();
        }}, {delay_ms});
    """)

def apply_css(stylesheet: str):
    """
    Adds a CSS style block to the page.
    """
    
    st.html(f"<style>{str(stylesheet)}</style>", width="content")

def classname_streamlit(class_name: str, unique: bool = True):
    """
    Returns a string pair for use in CSS styles as a class name.

    The first element is `class_name` with a UUID suffix if `unique` is True; it is used as the value for the `key` parameter of a Streamlit component.
    The second element is the CSS class name corresponding to the first element (with the `.st-key-...` prefix).
    """

    class_name += f"-{uuid4()}" if unique else ""
    return class_name, f".st-key-{class_name}"