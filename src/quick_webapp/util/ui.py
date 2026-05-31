from collections.abc import Callable, Mapping, Sequence
from typing import Any
import time
from uuid import uuid4
from pandas import DataFrame
import streamlit as st
from quick_webapp.data.data_view import DataView


def execute_javascript(script: str):
    """
    Adds JavaScript to the page.
    """

    wrapped_script = f"""
    <script>
        (function() {{
            {script}
        }})();
    </script>
    """
    st.components.v1.html(wrapped_script, height=0, width=0)


def write_cookie(key: str, value: str, max_age_seconds: int = 86400):
    """
    Writes a real HTTP cookie into the parent browser window.
    """
    
    execute_javascript(f'window.parent.document.cookie = "{key}={value}; max-age={max_age_seconds}; path=/;";')

def read_cookie(key: str) -> str | None:
    """
    Reads the cookie on the next rerun from the server side.
    """
    return st.context.cookies.get(key)


def console_log(value: str):
    """
    Adds JavaScript to the page to print a log message to the browser console.
    """

    st.html(f"<script>console.log('{str(value)}')</script>", unsafe_allow_javascript=True, width="content")


def console_warning(value: str):
    """
    Adds JavaScript to the page to print a warning log message to the browser console.
    """

    st.html(f"<script>console.warn('{str(value)}')</script>", unsafe_allow_javascript=True, width="content")


def console_error(value: str):
    """
    Adds JavaScript to the page to print an error log message to the browser console.
    """

    st.html(f"<script>console.error('{str(value)}')</script>", unsafe_allow_javascript=True, width="content")


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


def render_branched_fragment(
        predicate: bool,
        fragment_of_true: Callable[[], None],
        fragment_of_false: Callable[[], None],
        interval: float = 1.0
):
    """
    Renders a reactive element (`fragment_of_true` or `fragment_of_false`) on the current page based on `predicate`.

    If `predicate` is False, it pauses execution for `interval` seconds and triggers a rerun/update.
    """

    if predicate:
        fragment_of_true()
    else:
        fragment_of_false()
        time.sleep(interval)
        st.rerun()


def render(obj: Any, label: str | None = None):
    """
    Renders the object in a pretty-formatted way.
    """

    if obj is not None:
        span_label = (label + ": ") if label else ""
        if isinstance(obj, bool):
            st.write(span_label + ("☒" if obj else "☐"))

        elif isinstance(obj, (int, float)):
            st.markdown(f"{span_label}*{obj}*")

        elif isinstance(obj, str):
            if "\n" in obj or len(obj) > 64:
                st.code(obj, line_numbers=True, wrap_lines=True)
            else:
                st.markdown(obj)
        elif isinstance(obj, DataView):
            with st.expander(obj.label if obj.has_label else label):
                if obj.has_original:
                    st.json(obj.original, expanded=False)
                if obj.rows_length:
                    st.table(obj.rows)
                for section in obj.sections:
                    render(section)

        elif isinstance(obj, Mapping):
            if label:
                st.markdown(f"**{label}**")
            st.json(obj, expanded=False)

        elif isinstance(obj, Sequence) and all(isinstance(item, Mapping) for item in obj):
            if label:
                st.markdown(f"**{label}**")

            st.table(obj, hide_index=True)

        elif isinstance(obj, DataFrame):
            st.dataframe(obj, hide_index=True)

        else:
            st.write(span_label)
            st.write(repr(obj))
