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

def __render_diff_html(
    rows,
    line_numbers: bool,
    unchanged_lines_text: str,
) -> str:
    rendered = []

    signs = {
        "context": " ",
        "removed": "−",
        "added": "+",
    }

    for kind, old_no, new_no, text in rows:
        if kind == "separator":
            rendered.append(
                f'<div class="diff-separator">'
                f'⋯ {html.escape(unchanged_lines_text)} ⋯'
                f'</div>'
            )
            continue

        old_number = (
            str(old_no) if line_numbers and old_no is not None else ""
        )
        new_number = (
            str(new_no) if line_numbers and new_no is not None else ""
        )

        sign = signs[kind]
        content = html.escape(text)

        rendered.append(
            f'<div class="diff-line {kind}">'
            f'<span class="line-number">{old_number}</span>'
            f'<span class="line-number">{new_number}</span>'
            f'<span class="sign">{sign}</span>'
            f'<span class="content">{content}</span>'
            f'</div>'
        )

    diff_html = "\n".join(rendered)
    container_class = "with-line-numbers" if line_numbers else "without-line-numbers"

    return f"""
    <style>
        .diff-container {{
            overflow: auto;
            font-family: monospace;
            font-size: 13px;
            border: 1px solid rgba(110, 118, 129, 0.15);
            border-radius: 0.5rem;
        }}

        .diff-line {{
            display: flex;
            min-width: max-content;
            padding: 0 8px;
            white-space: pre;
            line-height: 1.6;
        }}

        .line-number {{
            display: inline-block;
            width: 42px;
            flex-shrink: 0;
            text-align: right;
            padding-right: 8px;
            color: #888;
            user-select: none;
        }}

        .diff-container.without-line-numbers .line-number {{
            display: none;
        }}

        .sign {{
            display: inline-block;
            width: 20px;
            flex-shrink: 0;
            user-select: none;
        }}

        .content {{
            flex: 1;
        }}

        .added {{
            background: rgba(46, 160, 67, 0.20);
        }}

        .removed {{
            background: rgba(248, 81, 73, 0.20);
        }}

        .added .sign {{
            color: #2da44e;
            font-weight: bold;
        }}

        .removed .sign {{
            color: #f85149;
            font-weight: bold;
        }}

        .diff-line.context {{
            background: rgba(240, 240, 240, 0.66);
        }}

        .diff-separator {{
            padding: 6px 12px;
            color: #8b949e;
            background: rgba(110, 118, 129, 0.15);
            text-align: center;
            user-select: none;
        }}
    </style>

    <div class="diff-container {container_class}">
        {diff_html}
    </div>
    """

def render_text_diff(
    old_text: str,
    new_text: str,
    line_numbers: bool = False,
    context_lines: int | None = 3,
    unchanged_lines_next: str = "unchanged lines omitted"
) -> None:
    """
    Renders git-like diff view, optionally showing line numbers.

    If line_numbers is truely value then line numbers for each comparing element are displayed.

    If context_lines is present and positive then maximum amount if the same rows that about to be displayed is equal this value.
    """

    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    if not line_numbers or context_lines is None:
        effective_context = max(len(old_lines), len(new_lines))
    else:
        effective_context = context_lines

    matcher = difflib.SequenceMatcher(
        None,
        old_lines,
        new_lines,
        autojunk=False,
    )
    opcodes = matcher.get_opcodes()

    changes = [
        idx
        for idx, (tag, *_rest) in enumerate(opcodes)
        if tag != "equal"
    ]

    if not changes:
        if old_lines:
            st.html(__render_diff_html([("context", i + 1, i + 1, old_lines[i]) for i in range(len(old_lines))], line_numbers, unchanged_lines_next))
        return

    groups = []

    for idx in changes:
        tag, i1, i2, j1, j2 = opcodes[idx]

        start_old = max(0, i1 - effective_context)
        start_new = max(0, j1 - effective_context)
        end_old = min(len(old_lines), i2 + effective_context)
        end_new = min(len(new_lines), j2 + effective_context)

        if groups:
            previous = groups[-1]

            if start_old <= previous["end_old"] and start_new <= previous["end_new"]:
                previous["end_old"] = max(previous["end_old"], end_old)
                previous["end_new"] = max(previous["end_new"], end_new)
                previous["last_opcode"] = idx
                continue

        groups.append({
            "start_old": start_old,
            "start_new": start_new,
            "end_old": end_old,
            "end_new": end_new,
            "first_opcode": idx,
            "last_opcode": idx,
        })

    rows = []

    for group_index, group in enumerate(groups):
        start_old = group["start_old"]
        start_new = group["start_new"]
        end_old = group["end_old"]
        end_new = group["end_new"]

        if group_index == 0 and (start_old > 0 or start_new > 0):
            rows.append(("separator", None, None, "..."))

        if group_index > 0:
            rows.append(("separator", None, None, "..."))

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                left = max(i1, start_old)
                right = min(i2, end_old)

                if left >= right:
                    continue

                for old_idx in range(left, right):
                    new_idx = j1 + (old_idx - i1)

                    if start_new <= new_idx < end_new:
                        rows.append((
                            "context",
                            old_idx + 1,
                            new_idx + 1,
                            old_lines[old_idx],
                        ))

            elif tag == "delete":
                if i1 >= start_old and i2 <= end_old:
                    for old_idx in range(i1, i2):
                        rows.append((
                            "removed",
                            old_idx + 1,
                            None,
                            old_lines[old_idx],
                        ))

            elif tag == "insert":
                if j1 >= start_new and j2 <= end_new:
                    for new_idx in range(j1, j2):
                        rows.append((
                            "added",
                            None,
                            new_idx + 1,
                            new_lines[new_idx],
                        ))

            elif tag == "replace":
                if i1 >= start_old and i2 <= end_old:
                    for old_idx in range(i1, i2):
                        rows.append((
                            "removed",
                            old_idx + 1,
                            None,
                            old_lines[old_idx],
                        ))

                if j1 >= start_new and j2 <= end_new:
                    for new_idx in range(j1, j2):
                        rows.append((
                            "added",
                            None,
                            new_idx + 1,
                            new_lines[new_idx],
                        ))

        if group_index == len(groups) - 1 and (
            end_old < len(old_lines) or end_new < len(new_lines)
        ):
            rows.append(("separator", None, None, "..."))

    st.html(__render_diff_html(rows, line_numbers, unchanged_lines_next))

