from collections.abc import Callable, Mapping, Sequence
from typing import Any
import time
from pandas import DataFrame
import difflib
import html
import streamlit as st
from quick_webapp.util.data.data_view import DataView
from quick_webapp.util.commons import extract_exception_messages


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

def render_exception_messages(e: BaseException, starter_message: str | None = None):
    """
    Renders exception message and its caused exception messages in Streamlit.error(...)
    """

    st.error("\n\n".join(extract_exception_messages(e, starter_message)))

def render_text_diff(
    old_text: str,
    new_text: str,
) -> None:
    """
    Renders git-like diff view.
    """

    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    diff = difflib.ndiff(old_lines, new_lines)

    rows = []

    for line in diff:
        if line.startswith("? "):
            continue

        prefix = line[:2]
        content = html.escape(line[2:])

        if prefix == "  ":
            rows.append(
                f'<div class="diff-line context">'
                f'<span class="sign"> </span>'
                f'<span>{content}</span>'
                f'</div>'
            )

        elif prefix == "- ":
            rows.append(
                f'<div class="diff-line removed">'
                f'<span class="sign">−</span>'
                f'<span>{content}</span>'
                f'</div>'
            )

        elif prefix == "+ ":
            rows.append(
                f'<div class="diff-line added">'
                f'<span class="sign">+</span>'
                f'<span>{content}</span>'
                f'</div>'
            )

    diff_html = "\n".join(rows)

    st.html(
        f"""
        <style>
            .diff-container {{
                overflow: auto;
            }}

            .diff-line {{
                display: flex;
                min-width: max-content;
                padding: 0 8px;
                white-space: pre;
            }}

            .diff-line .sign {{
                display: inline-block;
                width: 20px;
                flex-shrink: 0;
                user-select: none;
            }}

            .diff-line.added {{
                background: rgba(46, 160, 67, 0.20);
            }}

            .diff-line.removed {{
                background: rgba(248, 81, 73, 0.20);
            }}

            .diff-line.added .sign {{
                color: #2da44e;
                font-weight: bold;
            }}

            .diff-line.removed .sign {{
                color: #f85149;
                font-weight: bold;
            }}

            .diff-line.context {{
                opacity: 0.8;
            }}
        </style>

        <div class="diff-container">
            {diff_html}
        </div>
        """,
        unsafe_allow_javascript=True
    )

