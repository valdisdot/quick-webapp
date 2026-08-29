from collections.abc import Callable, Mapping, Sequence, Iterable
from typing import Any
import time
from uuid import uuid4
from pandas import DataFrame
import streamlit as st
from quick_webapp.util.data.data_view import DataView


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


def action_table(
        data: Iterable[Any], 
        data_mappers: dict[str, Callable[[Any], None]], 
        action_mappers: dict[str, Callable[[Any], None]], 
        actions_col_label: str = None, 
        action_button_type: str = "secondary",
        table_head_line_color: str = "silver",
        container_border: bool = True, 
        container_width: str | int = "stretch", 
        data_to_action_column_ratios: int | list[int] = 3
):
    """
    Renders data as an action table. On the left it renders data element as a components, based on data_mappers, on the right - action buttons using action_mappers.

    data - the data to render
    data_mappers - a dictionary where key is used as a column name, value as a callable that will be invoked for the column on each data element.
    action_mappers - a dcitionary where key is used as a button label, value as a callback on the button clicked.
    actions_col_label - a column name (for the first column) for action buttons.
    action_button_type - Streamlit button type for action buttons: 'primary', 'secondary', 'tertiary'
    table_head_line_color - line color between table head and rendered data (no separator if falsy)
    container_border - flag to wrap table container in the border
    container_width - width of the table container, Streamlit constant ('stretch', 'content') or integer
    data_to_action_column_ratios - a column ration configuration, for a number it defines how much data column is bigger that action column (X to 1), for a list the list is used for st.culumns directly.
    """

    container = st.container(border = container_border, width=container_width, gap="xxsmall")

    if (isinstance(data_to_action_column_ratios, Iterable)):
        dif = len(data_mappers) + len(action_mappers) - len(data_to_action_column_ratios)
        if dif > 0:
            data_to_action_column_ratios.append(1)
        
    else:  
        data_to_action_column_ratios = (
            [data_to_action_column_ratios] * len(data_mappers) + [1] * len(action_mappers)
        )

    with container:
        header = st.columns(
            data_to_action_column_ratios,
            gap="xxsmall",
            vertical_alignment="center"
        )

        if table_head_line_color:
            st.html(f'<hr style="background-color: {table_head_line_color}; border: none; height: 1px">')

    for col, title in zip(header, data_mappers.keys()):
        with col:
            st.markdown(f"**{title}**")

    if actions_col_label and action_mappers:
        header[len(data_mappers)].write(f"**{actions_col_label}**")

    for row_i, obj in enumerate(data):
        with container:
            row = st.columns(
                data_to_action_column_ratios,
                gap="xxsmall",
                vertical_alignment="center",
            )

        for col, data_render in zip(row, data_mappers.values()):
            with col:
                data_render(obj)

        for action_i, (action_label, action) in enumerate(action_mappers.items()):
            with row[len(data_mappers) + action_i]:
                if st.button(
                    action_label,
                    key=f"{row_i}-{action_label}",
                    width="stretch",
                    type=action_button_type
                ):
                    action(obj)

def render_exception_messages(e: BaseException, starter_message: str | None = None):
    """
    Renders exception message and its caused exception messages in Streamlit.error(...)
    """

    messages = []
    if starter_message:
        messages.append(starter_message)
    seen = set()
    current_exception = e

    while current_exception is not None and id(current_exception) not in seen:
        seen.add(id(current_exception))
        message = str(current_exception).strip()
        if message:
            messages.append(message)

        if current_exception.__cause__ is not None:
            current_exception = current_exception.__cause__
            continue

        if current_exception.__context__ is not None and not current_exception.__suppress_context__:
            current_exception = current_exception.__context__
            continue

        break

    st.error("\n".join(messages))
