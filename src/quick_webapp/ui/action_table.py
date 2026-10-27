from collections.abc import Callable, Sequence, Iterable
from typing import Any
import streamlit as st

def action_table(
        data: Iterable[Any], 
        no_data_message: str,
        data_mappers: dict[str, Callable[[Any], None]], 
        action_mappers: dict[str, Callable[[Any], None]], 
        actions_col_label: str = None, 
        action_button_type: str = None,
        action_menu_label: str = None,
        table_head_line_color: str = "silver",
        container_border: bool = True, 
        container_width: str | int = "stretch", 
        column_ratio_spec: list[int] = None,
        column_gap: str = "xxsmall",
        column_vertical_alignment: str = "center",
        key_suffix: str = ""
):
    """
    Renders data as an action table. On the left it renders data element as a components, based on data_mappers, on the right - action buttons using action_mappers.

    data: the data to render

    no_data_message = a line to be displayed if data is falsy

    data_mappers: a dictionary where key is used as a column name, value as a callable that accepts the data element and renders the data (must be compatible to write inside the streamlit.column element)

    action_mappers: a dicitionary where key is used as a button label, value as a callback on the button clicked (a function that simply accept the data element).

    actions_col_label: a column name (for the first column) for action buttons.

    action_button_type: Streamlit button type for action buttons ('primary', 'secondary', 'tertiary'), if the value is present then action elements is buttons, if neither this value nor action_menu_label are present then set to 'secondary' implicitelly by Streamlit

    action_menu_label: a label for a menu button, ignored if action_button_type is present, if the value is present then action elements is menu buttons

    table_head_line_color: line color between table head and rendered data (no separator if falsy)

    container_border: flag to wrap table container in the border
    
    container_width: width of the table container, Streamlit constant ('stretch', 'content') or an integer

    column_ratio_spec: a column ratio specs (in case of falsy value the columns will be distributed evenly, in case the length is less than sum of lenghts of data_mappers and action_mappers will be added 1 to fulfill the spec)

    column_gap: a parament for streamlit.column for gap ('xxsmall', 'xsmall', 'small', 'medium', 'large', 'xlarge', 'xxlarge')

    column_vertical_alignment: a parament for streamlit.column for vertical_alignment ('top', 'center', or 'bottom')

    """

    container = st.container(border = container_border, width=container_width, gap=column_gap)
    action_control_type = "button" if action_button_type or not action_menu_label else "menu"
    action_button_type = action_button_type if action_button_type else "secondary"

    action_spec_scalar = len(action_mappers) if action_control_type == "button" else (1 if action_mappers else 0)
    if not column_ratio_spec or not isinstance(column_ratio_spec, Sequence):
        column_ratio_spec = [1] * (len(data_mappers) + action_spec_scalar)

    else:
        shortfall = len(data_mappers) + action_spec_scalar - len(column_ratio_spec)
        while shortfall > 0:
            column_ratio_spec.append(1)
            shortfall -= 1

    with container:
        header = st.columns(
            column_ratio_spec,
            gap=column_gap,
            vertical_alignment=column_vertical_alignment,
        )

        if table_head_line_color:
            st.html(f'<hr style="background-color: {table_head_line_color}; border: none; height: 1px">')

    for column, title in zip(header, data_mappers.keys()):
        with column:
            st.markdown(f"**{title}**")

    if actions_col_label and action_mappers:
        header[len(data_mappers)].write(f"**{actions_col_label}**")

    if data:
        for row_index, data_element in enumerate(data):
            with container:
                row_columns = st.columns(
                    column_ratio_spec,
                    gap=column_gap,
                    vertical_alignment=column_vertical_alignment
                )

            for column, data_render in zip(row_columns, data_mappers.values()):
                with column:
                    data_render(data_element)
            if action_control_type == "button":
                for action_index, (action_label, action) in enumerate(action_mappers.items()):
                    with row_columns[len(data_mappers) + action_index]:
                        if st.button(
                            action_label,
                            key=f"{row_index}-{action_label}-{key_suffix}",
                            width="stretch",
                            type=action_button_type
                        ):
                            action(data_element)
            else:
                with row_columns[len(data_mappers)]:
                    selected_action = st.menu_button(
                        action_menu_label,
                        options=action_mappers.keys(),
                        key=f"{row_index}-action_label-{key_suffix}",
                        width="stretch",
                    )
                    if selected_action:
                        action_mappers[selected_action](data_element)

    elif no_data_message:
        st.write(no_data_message)