from __future__ import annotations
from typing import Any, Literal
from uuid import uuid4
import streamlit as st
from quick_webapp import bean

class Node:
    """
    Internal representation of one node.

    `id` is deliberately independent from the node's location in the tree.
    It is used exclusively for stable Streamlit widget keys.
    """

    def __init__(self, value: Any | Node, parent: Node):
        self.__value = value
        self.__parent = parent
        self.__id = uuid4().hex
        self.__included = True

    @staticmethod
    def create(data: Any, parent: Node | None = None) -> Node:
        """
        Convert ordinary Python data into the internal tree.

        If parent is None then it is a root node.
        """

        if data is None:
            return Node(None, parent)

        if isinstance(data, dict):
            dict_node = Node({}, parent)
            for key, data_item in data.items():
                dict_node.add_object_element(data_item, key)
            return dict_node

        if isinstance(data, list):
            list_node = Node([], parent)
            for data_item in data:
                list_node.add_array_element(data_item)
            return list_node

        return Node(data, parent)

    @property
    def value(self) -> Any:
        return self.__value

    @value.setter
    def value(self, value: Any) -> None:
        self.__value = value

    @property
    def id(self) -> str:
        return self.__id

    @property
    def parent(self) -> Node | None:
        return self.__parent

    @property
    def is_root(self) -> bool:
        return self.__parent is None

    @property
    def is_array(self) -> bool:
        return isinstance(self.__value, list)

    @property
    def is_object(self) -> bool:
        return isinstance(self.__value, dict)

    @property
    def included(self) -> bool:
        return self.__included

    @included.setter
    def included(self, value: bool) -> None:
        self.__included = value

    def data(self) -> Any:
        """
        Converts the internal tree back to ordinary Python data.

        Values from object and array nodes will be included for children with included flag, in case of the leaf node it always returns its value (if the root node is a scalar the value can't be ignored)
        """

        if isinstance(self.__value, dict):
                return {
                    key: child.data() for key, child in self.__value.items() if child.__included
                }

        if isinstance(self.__value, list):
                return [
                    child.data() for child in self.__value if child.__included
                ]

        return self.__value

    def add_object_element(self, data: Any = None, base_field_name = "new_field") -> None:
        """
        Add a new field to an object.

        data is a Python value or none (will be creaded a field with an empty string).

        If base_field_name exists, iterated one will be created, e.g. base_field_name_1 and so on.

        If Node.value is not dict then does nothing.
        """

        if not isinstance(self.__value, dict):
            return

        name = base_field_name
        index = 1

        while name in self.__value:
            name = f"{base_field_name}_{index}"
            index += 1

        self.__value[name] = Node.create(data, self)

    def push_object_element(self, data: Any = None, base_field_name = "new_field") -> None:
        """
        Push a new field to an object at the beginning.

        data is a Python value or none (will be creaded a field with an empty string).

        If base_field_name exists, iterated one will be created, e.g. base_field_name_1 and so on.

        If Node.value is not dict then does nothing.
        """

        if isinstance(self.__value, dict):
            name = base_field_name
            index = 1

            while name in self.__value:
                name = f"{base_field_name}_{index}"
                index += 1

            new_value: dict[str, Node] = {name: Node.create(data, self)}
            new_value.update(self.__value)

            self.__value = new_value

    def add_array_element(self, data: Any = None) -> None:
        """
        Add a new item to an array.

        data is a Python value or none.

        If Node.value is not a list then does nothing.
        """

        if isinstance(self.__value, list):
            self.__value.append(Node.create(data, self))

    def push_array_element(self, data: Any = None) -> None:
        """
        Push a new item to an array at the beginning.

        data is a Python value or none.

        If Node.value is not a list then does nothing.
        """

        if isinstance(self.__value, list):
            self.__value.insert(0, Node.create(data, self))

    def add_object_sibling_element(self, sibling_field_name: str, data: Any = None, base_field_name = "new_field") -> None:
        """
        Add a new field before/after an existing object field sibling_field_name.

        If sibling_field_name is absent, add_dict_field method will be used.

        data is a Python value or none.

        If base_field_name exists, iterated one will be created, e.g. base_field_name_1 and so on.

        If Node.value is not dict then does nothing.
        """

        if isinstance(self.__value, dict):
                name = base_field_name
                index = 1

                while name in self.__value:
                    name = f"{base_field_name}_{index}"
                    index += 1

                if sibling_field_name in self.__value:
                    new_value: dict[str, Node] = {}

                    for key, value in self.__value.items():
                        new_value[key] = value
                        if key == sibling_field_name:
                            new_value[name] = Node.create(data, self)

                    self.__value = new_value

                else:
                    self.add_object_element(data, name)

    def add_array_sibling_element(self, index: int, data: Any = None) -> None:
        """
        Add a new item before/after an existing array item.

        data is a Python value or none.

        If Node.value is not a list then does nothing.
        """

        if isinstance(self.__value, list):
            self.__value.insert(index + 1, Node.create(data, self))

    def delete_element(self, node_key: str | int) -> None:
        """
        Delete an element.
        """

        self.__value.pop(node_key)

    def contains_node_key(self, node_key: str | int):
        """
        Check is the key is inside the inner Node structure.

        Always false if Node has no inner structure.
        """

        if isinstance(self.__value, list):
            return len(self.__value) > node_key

        if isinstance(self.__value, dict):
            return (node_key in self.__value)

        return False

    def rename_dict_element_key(self, field_name: str, new_field_name: str) -> None:
        """
        Rename element from field_name to new_field_name inside the dict Node structure.

        Does nothing if key is not in the dict Node structure, new key is already taken or there is no dict structure.
        """

        if isinstance(self.__value, dict) and field_name in self.__value and new_field_name not in self.__value:
            new_value: dict[str, Node] = {}

            for key, value in self.__value.items():
                if key == field_name:
                    new_value[new_field_name] = value

                else:
                    new_value[key] = value

            self.__value = new_value


def __make_widget_key(
    editor_key: str,
    node: Node,
    suffix: str
) -> str:
    return f"{editor_key}_{node.id}_{suffix}"

@bean(key="__bool_list_structure_editor")
def __bool_list() -> list[str]:
    return ["false", "true"]

def __render_structure_editor_scalar(
    editor_key: str,
    node: Node,
) -> None:
    value = node.value

    if value is None:
        st.text_input(
            "Value", 
            value="null", 
            key=__make_widget_key(editor_key, node, "null"),
            disabled=True, 
            label_visibility="collapsed"
        )

    elif isinstance(value, bool):
        node.value = st.selectbox(
            "Value",
            options=__bool_list(),
            index=int(value),
            key=__make_widget_key(editor_key, node, "bool"),
            label_visibility="collapsed",
            width=70
        ) == "true"

    elif isinstance(value, int):
        node.value = st.number_input(
            "Value",
            value=value,
            step=1,
            key=__make_widget_key(editor_key, node, "int"),
            label_visibility="collapsed"
        )

    elif isinstance(value, float):
        node.value = st.number_input(
            "Value",
            value=value,
            key=__make_widget_key(editor_key, node, "float"),
            label_visibility="collapsed"
        )

    else:
        node.value = st.text_input(
            "Value",
            value=str(value),
            key=__make_widget_key(editor_key, node, "string"),
            label_visibility="collapsed"
        )

def __render_structure_editor_scalar_row(
    editor_key: str,
    node: Node,
    node_key: str | int | None,
    spec_for_scalar_of_dict: list[int | float],
    spec_for_scalar_of_arrays: list[int | float],
    include_help: str,
    field_empty_error_text: str,
    field_exists_error_text: str,
    add_string_menu_text: str,
    add_int_menu_text: str,
    add_float_menu_text: str,
    add_bool_menu_text: str,
    add_null_menu_text: str,
    add_object_menu_text: str,
    add_array_menu_text: str,
    clone_menu_text: str, 
    delete_menu_text: str
) -> None:
        if node.parent.is_object: # object items
            columns = st.columns(
                spec_for_scalar_of_dict,
                vertical_alignment="top",
                gap="xxsmall"
            )

            with columns[0]:
                field_name = str(node_key)

                new_field_name = st.text_input(
                    "Field",
                    value=field_name,
                    key=__make_widget_key(editor_key, node, "name"),
                    label_visibility="collapsed"
                )

                if new_field_name != field_name:
                    if not new_field_name:
                        st.badge("⚠️", color="yellow", help=field_empty_error_text)

                    elif node.parent.contains_node_key(new_field_name):
                        st.badge("⚠️", color="yellow", help=field_exists_error_text)

                    else:
                        node.parent.rename_dict_element_key(node_key, new_field_name)

            with columns[1]:
                with st.container(horizontal=True, vertical_alignment="top"):
                    __render_structure_editor_scalar(editor_key, node)
                    node.included = st.checkbox(" ", node.included, help=include_help if include_help else None, key=__make_widget_key(editor_key, node, "included"), label_visibility="visible" if include_help else "collapsed")
                    st.space(size="xxsmall")

            with columns[2]:
                new_sibling_type = st.menu_button(
                    "⯇", 
                    (add_string_menu_text, add_int_menu_text, add_float_menu_text, add_bool_menu_text, add_null_menu_text, add_object_menu_text, add_array_menu_text, clone_menu_text, delete_menu_text),  
                    key=__make_widget_key(editor_key, node, "add_sibling"),
                    width="stretch"
                )

                if new_sibling_type:
                    if new_sibling_type == add_string_menu_text:
                        node.parent.add_object_sibling_element(field_name, "")
                    elif new_sibling_type == add_int_menu_text:
                        node.parent.add_object_sibling_element(field_name, 0)
                    elif new_sibling_type == add_float_menu_text:
                        node.parent.add_object_sibling_element(field_name, 0.0)
                    elif new_sibling_type == add_bool_menu_text:
                        node.parent.add_object_sibling_element(field_name, False)
                    elif new_sibling_type == add_null_menu_text:
                        node.parent.add_object_sibling_element(field_name)
                    elif new_sibling_type == add_object_menu_text:
                        node.parent.add_object_sibling_element(field_name, {})
                    elif new_sibling_type == add_array_menu_text:
                        node.parent.add_object_sibling_element(field_name, [])
                    elif new_sibling_type == clone_menu_text:
                        node.parent.add_object_sibling_element(field_name, node.data(), field_name)
                    else:
                        node.parent.delete_element(field_name)

                    st.rerun(scope="fragment")

        else: # array elements
            columns = st.columns(
                spec_for_scalar_of_arrays,
                vertical_alignment="top",
                gap="xxsmall"
            )

            with columns[0]:
                st.caption(f"[{node_key}]", width="content")

            with columns[1]:
                with st.container(horizontal=True, vertical_alignment="top"):
                    __render_structure_editor_scalar(editor_key, node)
                    node.included = st.checkbox(" ", node.included, help=include_help if include_help else None, key=__make_widget_key(editor_key, node, "included"), label_visibility="visible" if include_help else "collapsed")
                    st.space(size="xxsmall")

            with columns[2]:
                new_sibling_type = st.menu_button(
                    "⯇", 
                    (add_string_menu_text, add_int_menu_text, add_float_menu_text, add_bool_menu_text, add_null_menu_text, add_object_menu_text, add_array_menu_text, clone_menu_text, delete_menu_text),  
                    key=__make_widget_key(editor_key, node, "add_sibling"),
                    width="stretch"
                )

                if new_sibling_type:
                    if new_sibling_type == add_string_menu_text:
                        node.parent.add_array_sibling_element(node_key, "")
                    elif new_sibling_type == add_int_menu_text:
                        node.parent.add_array_sibling_element(node_key, 0)
                    elif new_sibling_type == add_float_menu_text:
                        node.parent.add_array_sibling_element(node_key, 0.0)
                    elif new_sibling_type == add_bool_menu_text:
                        node.parent.add_array_sibling_element(node_key, False)
                    elif new_sibling_type == add_null_menu_text:
                        node.parent.add_array_sibling_element(node_key)
                    elif new_sibling_type == add_object_menu_text:
                        node.parent.add_array_sibling_element(node_key, {})
                    elif new_sibling_type == add_array_menu_text:
                        node.parent.add_array_sibling_element(node_key, [])
                    elif new_sibling_type == clone_menu_text:
                        node.parent.add_array_sibling_element(node_key, node.data())
                    else:
                        node.parent.delete_element(node_key)
                    
                    st.rerun(scope="fragment")

def __render_structure_editor_object(
    editor_key: str,
    node: Node,
    expand: bool,
    collapse: bool,
    node_key: str | int | None,
    spec_for_objects: list[int | float],
    spec_for_arrays: list[int | float],
    spec_for_scalar_of_dict: list[int | float],
    spec_for_scalar_of_arrays: list[int | float],
    expander_help: str,
    expand_all_help: str,
    collapse_all_help: str,
    include_help: str,
    field_empty_error_text: str,
    field_exists_error_text: str,
    add_string_menu_text: str,
    add_int_menu_text: str,
    add_float_menu_text: str,
    add_bool_menu_text: str,
    add_null_menu_text: str,
    add_object_menu_text: str,
    add_array_menu_text: str,
    clone_menu_text: str,
    delete_menu_text: str,
    context: dict[str, Any]
) -> None:

    with st.container(border=True, vertical_alignment="top", key=__make_widget_key(editor_key, node, "object")):
        expand_key = __make_widget_key(editor_key, node, "expander")

        if not node.is_root:
            with st.container(horizontal=True, vertical_alignment="center"):
                if expand:
                    context[expand_key] = True
                elif collapse:
                    context[expand_key] = False

                expanded = context.get(expand_key, False)

                if st.button(":material/collapse_all:" if expanded else ":material/expand_all:", key=expand_key):
                    context[expand_key] = not expanded
                    st.rerun(scope="fragment")

                field_name = "$" if node.is_root else node_key
                disabled = node.is_root or node.parent.is_array

                new_field_name = st.text_input(
                    "Field",
                    value=str(field_name),
                    key=__make_widget_key(editor_key, node, "name"),
                    label_visibility="collapsed",
                    disabled=disabled
                )

                if not disabled and new_field_name != field_name:
                    if not new_field_name:
                        st.badge("⚠️", color="yellow", help=field_empty_error_text)

                    elif node.parent.contains_node_key(new_field_name):
                        st.badge("⚠️", color="yellow", help=field_exists_error_text)

                    else:
                        node.parent.rename_dict_element_key(node_key, new_field_name)

                node.included = st.checkbox(" ", node.included, help=include_help if include_help else None, key=__make_widget_key(editor_key, node, "included"), label_visibility="visible" if include_help else "collapsed")

        if node.is_root or context.get(expand_key):
            with st.container(horizontal=True, gap="xxsmall"):
                pushed_item_type = st.menu_button(
                    "⯆", 
                    (add_string_menu_text, add_int_menu_text, add_float_menu_text, add_bool_menu_text, add_null_menu_text, add_object_menu_text, add_array_menu_text), 
                    key=__make_widget_key(editor_key, node, "push_field"),
                    width="stretch"
                )

                expand = st.button(":material/expand_all:", help=expand_all_help, key=__make_widget_key(editor_key, node, "expand_all")) or expand
                collapse = st.button(":material/collapse_all:", help=collapse_all_help, key=__make_widget_key(editor_key, node, "collapse_all")) or collapse

            if pushed_item_type:
                if pushed_item_type == add_string_menu_text:
                    node.push_object_element("")
                elif pushed_item_type == add_int_menu_text:
                    node.push_object_element(0)
                elif pushed_item_type == add_float_menu_text:
                    node.push_object_element(0.0)
                elif pushed_item_type == add_bool_menu_text:
                    node.push_object_element(False)
                elif pushed_item_type == add_null_menu_text:
                    node.push_object_element()
                elif pushed_item_type == add_object_menu_text:
                    node.push_object_element({})
                elif pushed_item_type == add_array_menu_text:
                    node.push_object_element([])

                st.rerun(scope="fragment")
        
            with st.container(gap="xsmall"):
                for child_field_name, child in list(node.value.items()):
                    if isinstance(child.value, (dict, list)):
                        columns = st.columns(
                            spec_for_objects,
                            vertical_alignment="top",
                            gap="xxsmall"
                        )

                        with columns[0]:
                            __render_structure_editor_node(
                                editor_key,
                                child,
                                expand,
                                collapse,
                                child_field_name,
                                spec_for_objects,
                                spec_for_arrays,
                                spec_for_scalar_of_dict,
                                spec_for_scalar_of_arrays,
                                expander_help,
                                expand_all_help,
                                collapse_all_help,
                                include_help,
                                field_empty_error_text,
                                field_exists_error_text,
                                add_string_menu_text, 
                                add_int_menu_text, 
                                add_float_menu_text, 
                                add_bool_menu_text, 
                                add_null_menu_text, 
                                add_object_menu_text, 
                                add_array_menu_text, 
                                clone_menu_text,
                                delete_menu_text,
                                context
                            )

                        with columns[1]:
                            new_sibling_type = st.menu_button(
                                "⯇", 
                                (add_string_menu_text, add_int_menu_text, add_float_menu_text, add_bool_menu_text, add_null_menu_text, add_object_menu_text, add_array_menu_text, clone_menu_text, delete_menu_text), 
                                key=__make_widget_key(editor_key, child, "insert_next_field"),
                                width="stretch"
                            )

                            if new_sibling_type:
                                if new_sibling_type == add_string_menu_text:
                                    node.add_object_sibling_element(child_field_name, "")
                                elif new_sibling_type == add_int_menu_text:
                                    node.add_object_sibling_element(child_field_name, 0)
                                elif new_sibling_type == add_float_menu_text:
                                    node.add_object_sibling_element(child_field_name, 0.0)
                                elif new_sibling_type == add_bool_menu_text:
                                    node.add_object_sibling_element(child_field_name, False)
                                elif new_sibling_type == add_null_menu_text:
                                    node.add_object_sibling_element(child_field_name)
                                elif new_sibling_type == add_object_menu_text:
                                    node.add_object_sibling_element(child_field_name, {})
                                elif new_sibling_type == add_array_menu_text:
                                    node.add_object_sibling_element(child_field_name, [])
                                elif new_sibling_type == clone_menu_text:
                                    node.add_object_sibling_element(child_field_name, child.data(), child_field_name)
                                else:
                                    node.delete_element(child_field_name)

                                st.rerun(scope="fragment")

                    else:
                        __render_structure_editor_scalar_row(
                            editor_key,
                            child,
                            child_field_name,
                            spec_for_scalar_of_dict,
                            spec_for_scalar_of_arrays,
                            include_help,
                            field_empty_error_text,
                            field_exists_error_text,
                            add_string_menu_text, 
                            add_int_menu_text, 
                            add_float_menu_text, 
                            add_bool_menu_text, 
                            add_null_menu_text, 
                            add_object_menu_text, 
                            add_array_menu_text, 
                            clone_menu_text,
                            delete_menu_text
                        )

            added_item_type = st.menu_button(
                "⯅", 
                (add_string_menu_text, add_int_menu_text, add_float_menu_text, add_bool_menu_text, add_null_menu_text, add_object_menu_text, add_array_menu_text), 
                key=__make_widget_key(editor_key, node, "add_field"),
                width="stretch"
            )

            if added_item_type:
                if added_item_type == add_string_menu_text:
                    node.add_object_element("")
                elif added_item_type == add_int_menu_text:
                    node.add_object_element(0)
                elif added_item_type == add_float_menu_text:
                    node.add_object_element(0.0)
                elif added_item_type == add_bool_menu_text:
                    node.add_object_element(False)
                elif added_item_type == add_null_menu_text:
                    node.add_object_element()
                elif added_item_type == add_object_menu_text:
                    node.add_object_element({})
                elif added_item_type == add_array_menu_text:
                    node.add_object_element([])

                st.rerun(scope="fragment")

def __render_structure_editor_array(
    editor_key: str,
    node: Node,
    expand: bool,
    collapse: bool,
    node_key: str | int | None,
    spec_for_objects: list[int | float],
    spec_for_arrays: list[int | float],
    spec_for_scalar_of_dict: list[int | float],
    spec_for_scalar_of_arrays: list[int | float],
    expander_help: str,
    expand_all_help: str,
    collapse_all_help: str,
    include_help: str,
    field_empty_error_text: str,
    field_exists_error_text: str,
    add_string_menu_text: str,
    add_int_menu_text: str,
    add_float_menu_text: str,
    add_bool_menu_text: str,
    add_null_menu_text: str,
    add_object_menu_text: str,
    add_array_menu_text: str,
    clone_menu_text,
    delete_menu_text: str,
    context: dict[str, Any]
) -> None:

    with st.container(border=True, vertical_alignment="top", key=__make_widget_key(editor_key, node, "array")):
        expand_key = __make_widget_key(editor_key, node, "expander")

        if not node.is_root:
            with st.container(horizontal=True, vertical_alignment="center"):

                if expand:
                    context[expand_key] = True
                elif collapse:
                    context[expand_key] = False

                expanded = context.get(expand_key, False)

                if st.button(":material/collapse_all:" if expanded else ":material/expand_all:", key=expand_key):
                    context[expand_key] = not expanded
                    st.rerun(scope="fragment")

                st.caption(f"[{len(node.value)}]", width="content")

                field_name = "$" if node.is_root else node_key
                disabled = node.is_root or node.parent.is_array

                new_field_name = st.text_input(
                    "Field",
                    value=str(field_name),
                    key=__make_widget_key(editor_key, node, "name"),
                    label_visibility="collapsed",
                    disabled=disabled
                )

                if not disabled and new_field_name != field_name:
                    if not new_field_name:
                        st.badge("⚠️", color="yellow", help=field_empty_error_text)

                    elif node.parent.contains_node_key(new_field_name):
                        st.badge("⚠️", color="yellow", help=field_exists_error_text)

                    else:
                        node.parent.rename_dict_element_key(node_key, new_field_name)

                node.included = st.checkbox(" ", node.included, help=include_help if include_help else None, key=__make_widget_key(editor_key, node, "included"), label_visibility="visible" if include_help else "collapsed")

        if node.is_root or context.get(expand_key):
            with st.container(horizontal=True, gap="xxsmall"):
                pushed_item_type = st.menu_button(
                    "⯆", 
                    (add_string_menu_text, add_int_menu_text, add_float_menu_text, add_bool_menu_text, add_null_menu_text, add_object_menu_text, add_array_menu_text), 
                    key=__make_widget_key(editor_key, node, "push_element"),
                    width="stretch"
                )

                expand = st.button(":material/expand_all:", help=expand_all_help, key=__make_widget_key(editor_key, node, "expand_all")) or expand
                collapse = st.button(":material/collapse_all:", help=collapse_all_help, key=__make_widget_key(editor_key, node, "collapse_all")) or collapse

            if pushed_item_type:
                if pushed_item_type == add_string_menu_text:
                    node.push_array_element("")
                elif pushed_item_type == add_int_menu_text:
                    node.push_array_element(0)
                elif pushed_item_type == add_float_menu_text:
                    node.push_array_element(0.0)
                elif pushed_item_type == add_bool_menu_text:
                    node.push_array_element(False)
                elif pushed_item_type == add_null_menu_text:
                    node.push_array_element()
                elif pushed_item_type == add_object_menu_text:
                    node.push_array_element({})
                elif pushed_item_type == add_array_menu_text:
                    node.push_array_element([])

                st.rerun(scope="fragment")

            with st.container(gap="xsmall"):
                for child_index, child in enumerate(list(node.value)):
                    if isinstance(child.value, (dict, list)):
                        columns = st.columns(
                            spec_for_objects,
                            vertical_alignment="top",
                            gap="xxsmall"
                        )

                        with columns[0]:
                            __render_structure_editor_node(
                                editor_key,
                                child,
                                expand,
                                collapse,
                                child_index,
                                spec_for_objects,
                                spec_for_arrays,
                                spec_for_scalar_of_dict,
                                spec_for_scalar_of_arrays,
                                expander_help,
                                expand_all_help,
                                collapse_all_help,
                                include_help,
                                field_empty_error_text,
                                field_exists_error_text,
                                add_string_menu_text, 
                                add_int_menu_text, 
                                add_float_menu_text, 
                                add_bool_menu_text, 
                                add_null_menu_text, 
                                add_object_menu_text, 
                                add_array_menu_text, 
                                clone_menu_text,
                                delete_menu_text,
                                context
                            )

                        with columns[1]:
                            new_sibling_type = st.menu_button(
                                "⯇", 
                                (add_string_menu_text, add_int_menu_text, add_float_menu_text, add_bool_menu_text, add_null_menu_text, add_object_menu_text, add_array_menu_text, clone_menu_text, delete_menu_text), 
                                key=__make_widget_key(editor_key, child, "insert_next_field"),
                                width="stretch"
                            )

                            if new_sibling_type:
                                if new_sibling_type == add_string_menu_text:
                                    node.add_array_sibling_element(child_index, "")
                                elif new_sibling_type == add_int_menu_text:
                                    node.add_array_sibling_element(child_index, 0)
                                elif new_sibling_type == add_float_menu_text:
                                    node.add_array_sibling_element(child_index, 0.0)
                                elif new_sibling_type == add_bool_menu_text:
                                    node.add_array_sibling_element(child_index, False)
                                elif new_sibling_type == add_null_menu_text:
                                    node.add_array_sibling_element(child_index)
                                elif new_sibling_type == add_object_menu_text:
                                    node.add_array_sibling_element(child_index, {})
                                elif new_sibling_type == add_array_menu_text:
                                    node.add_array_sibling_element(child_index, [])
                                elif new_sibling_type == clone_menu_text:
                                    node.add_array_sibling_element(child_index, child.data())
                                else:
                                    node.delete_element(child_index)

                                st.rerun(scope="fragment")

                    else:
                        __render_structure_editor_scalar_row(
                            editor_key,
                            child,
                            child_index,
                            spec_for_scalar_of_dict,
                            spec_for_scalar_of_arrays,
                            include_help,
                            field_empty_error_text,
                            field_exists_error_text,
                            add_string_menu_text, 
                            add_int_menu_text, 
                            add_float_menu_text, 
                            add_bool_menu_text, 
                            add_null_menu_text, 
                            add_object_menu_text, 
                            add_array_menu_text, 
                            clone_menu_text,
                            delete_menu_text
                        )

            added_item_type = st.menu_button(
                "⯅", 
                (add_string_menu_text, add_int_menu_text, add_float_menu_text, add_bool_menu_text, add_null_menu_text, add_object_menu_text, add_array_menu_text), 
                key=__make_widget_key(editor_key, node, "add_element"),
                width="stretch"
            )

            if added_item_type:
                if added_item_type == add_string_menu_text:
                    node.add_array_element("")
                elif added_item_type == add_int_menu_text:
                    node.add_array_element(0)
                elif added_item_type == add_float_menu_text:
                    node.add_array_element(0.0)
                elif added_item_type == add_bool_menu_text:
                    node.add_array_element(False)
                elif added_item_type == add_null_menu_text:
                    node.add_array_element()
                elif added_item_type == add_object_menu_text:
                    node.add_array_element({})
                elif added_item_type == add_array_menu_text:
                    node.add_array_element([])

                st.rerun(scope="fragment")

def __render_structure_editor_node(
    editor_key: str,
    node: Node,
    expand: bool,
    collapse: bool,
    node_key: str | int | None,
    spec_for_objects: list[int | float],
    spec_for_arrays: list[int | float],
    spec_for_scalar_of_dict: list[int | float],
    spec_for_scalar_of_arrays: list[int | float],
    expander_help: str,
    expand_all_help: str,
    collapse_all_help: str,
    include_help: str,
    field_empty_error_text: str,
    field_exists_error_text: str,
    add_string_menu_text: str,
    add_int_menu_text: str,
    add_float_menu_text: str,
    add_bool_menu_text: str,
    add_null_menu_text: str,
    add_object_menu_text: str,
    add_array_menu_text: str,
    clone_menu_text: str,
    delete_menu_text: str,
    context: dict[str, Any]
) -> None:

    if node.is_object:
        __render_structure_editor_object(
            editor_key,
            node,
            expand,
            collapse,
            node_key,
            spec_for_objects,
            spec_for_arrays,
            spec_for_scalar_of_dict,
            spec_for_scalar_of_arrays,
            expander_help,
            expand_all_help,
            collapse_all_help,
            include_help,
            field_empty_error_text,
            field_exists_error_text,
            add_string_menu_text, 
            add_int_menu_text, 
            add_float_menu_text, 
            add_bool_menu_text, 
            add_null_menu_text, 
            add_object_menu_text, 
            add_array_menu_text, 
            clone_menu_text,
            delete_menu_text,
            context
        )

    elif node.is_array:
        __render_structure_editor_array(
            editor_key,
            node,
            expand,
            collapse,
            node_key,
            spec_for_objects,
            spec_for_arrays,
            spec_for_scalar_of_dict,
            spec_for_scalar_of_arrays,
            expander_help,
            expand_all_help,
            collapse_all_help,
            include_help,
            field_empty_error_text,
            field_exists_error_text,
            add_string_menu_text, 
            add_int_menu_text, 
            add_float_menu_text, 
            add_bool_menu_text, 
            add_null_menu_text, 
            add_object_menu_text, 
            add_array_menu_text, 
            clone_menu_text,
            delete_menu_text,
            context
        )

    else:
        __render_structure_editor_scalar_row(
            editor_key,
            node,
            node_key,
            spec_for_scalar_of_dict,
            spec_for_scalar_of_arrays,
            include_help,
            field_empty_error_text,
            field_exists_error_text,
            add_string_menu_text, 
            add_int_menu_text, 
            add_float_menu_text, 
            add_bool_menu_text, 
            add_null_menu_text, 
            add_object_menu_text, 
            add_array_menu_text, 
            clone_menu_text,
            delete_menu_text
        )

@st.fragment
def structure_editor(
    data: dict | list | Node,
    key: str,
    context: dict[str, Any],
    width: Literal["stretch", "content"] | int = "stretch",
    expander_help: str | None = None,
    expand_all_help: str | None = None,
    collapse_all_help: str | None = None,
    include_help: str | None = None,
    field_empty_error_text: str = "Field name is empty",
    field_exists_error_text: str = "Field name already exists",
    add_string_menu_text: str = "Add a string",
    add_int_menu_text: str = "Add an integer number",
    add_float_menu_text: str = "Add a floating number",
    add_bool_menu_text: str = "Add a boolean",
    add_null_menu_text: str = "Add null",
    add_object_menu_text: str = "Add an object",
    add_array_menu_text: str = "Add an array",
    clone_menu_text: str = "Clone",
    delete_menu_text: str = "Delete the field"
    
) -> Node:
    """
    Render an editable tree for a Python dict/list.

    Returns the root Node from the data with current editing. User can fetch data back using Node.data() method.

    data: root dict, list or Node. In case of Node, editor will be refreshed if the value changes (so user can set the editor by a new Node while it's opened)

    key: unique identifier for this editor instance.

    context: a dict for a data, so user can delete context[key] if needed to clear the structure_editor contextual data

    returns: a Node object with current data state that was created at context instantiation. This object also placed in context[key]["node"]
    """

    if key not in context:
        if isinstance(data, (dict, list)):
            data = Node.create(data)

        elif isinstance(data, Node):
            if not (data.is_object or data.is_array):
                raise TypeError("data Node must be an object or an array node as the root")

        else:
            raise TypeError(f"data must be dict, list or appropriate Node as the root, got {type(data)}")
        
        button_spec = 0.6
        context[key] = {
            "ui": {
                "spec_for_scalar_of_dict": [1, 4, button_spec],
                "spec_for_scalar_of_arrays": [0.3, 4.5, button_spec],
                "spec_for_objects": [5, button_spec],
                "spec_for_arrays": [5, button_spec]
            },
            "node": data
        }

    editor_context = context[key]
    root: Node = editor_context["node"]

    if isinstance(data, Node) and data != root:
        root = data
        editor_context["node"] = data

    with st.container(width=width):
        __render_structure_editor_node(
            key,
            root,
            False,
            False,
            None,
            editor_context["ui"]["spec_for_objects"],
            editor_context["ui"]["spec_for_arrays"],
            editor_context["ui"]["spec_for_scalar_of_dict"],
            editor_context["ui"]["spec_for_scalar_of_arrays"],
            expander_help,
            expand_all_help,
            collapse_all_help,
            include_help,
            field_empty_error_text,
            field_exists_error_text,
            add_string_menu_text, 
            add_int_menu_text, 
            add_float_menu_text, 
            add_bool_menu_text, 
            add_null_menu_text, 
            add_object_menu_text, 
            add_array_menu_text, 
            clone_menu_text,
            delete_menu_text,
            editor_context
        )

    return root

def __render_data_object(
    editor_key: str,
    node: Node,
    editor_context: dict,
    node_key: str | int
):
    widget_key = __make_widget_key(editor_key, node, "expanded")

    expanded = editor_context["expanded"].get(
        node.id,
        editor_context["default_expanded"]
    )

    with st.container(border=True, gap="xsmall"):
        if st.button(
            f"**{node_key}**",
            icon=f"{':material/collapse_all:' if expanded else ':material/expand_all:'}",
            key=widget_key,
            type="tertiary"
        ):
            editor_context["expanded"][node.id] = not expanded
            st.rerun(scope="fragment")

        if expanded:
            with st.container(gap="xsmall"):
                for field, child in node.value.items():
                    __render_data_node(
                    editor_key,
                    child,
                    editor_context,
                    field
                )

def __render_data_array(
    editor_key: str,
    node: Node,
    editor_context: dict,
    node_key: str | int
):
    widget_key = __make_widget_key(editor_key, node, "expanded")

    expanded = editor_context["expanded"].get(
        node.id,
        editor_context["default_expanded"]
    )

    with st.container(border=True, gap="xsmall"):
        if st.button(
            f"**{node_key}**",
            icon=f"{':material/collapse_all:' if expanded else ':material/expand_all:'}",
            key=widget_key,
            type="tertiary"
        ):
            editor_context["expanded"][node.id] = not expanded
            st.rerun(scope="fragment")

        if expanded:
            with st.container(gap="xsmall"):
                array_index_adjustment = editor_context["array_index_adjustment"]
                for index, child in enumerate(node.value):
                    __render_data_node(
                    editor_key,
                    child,
                    editor_context,
                    index + array_index_adjustment
                )
                    
def __render_data_scalar(
    editor_key: str,
    node: Node,
    node_key: str | int
):
    with st.container(horizontal=True, gap="xsmall", vertical_alignment="center"):
        st.write(f"**{node_key}:**")

        value = node.value

        if value is None:
            st.text_input(
                "Value", 
                value="null", 
                key=__make_widget_key(editor_key, node, "null"),
                disabled=True, 
                label_visibility="collapsed"
            )

        elif isinstance(value, bool):
            node.value = st.selectbox(
                "Value",
                options=__bool_list(),
                index=int(value),
                key=__make_widget_key(editor_key, node, "bool"),
                label_visibility="collapsed",
                width=70
            ) == "true"

        elif isinstance(value, int):
            node.value = st.number_input(
                "Value",
                value=value,
                step=1,
                key=__make_widget_key(editor_key, node, "int"),
                label_visibility="collapsed"
            )

        elif isinstance(value, float):
            node.value = st.number_input(
                "Value",
                value=value,
                key=__make_widget_key(editor_key, node, "float"),
                label_visibility="collapsed"
            )

        else:
            node.value = st.text_input(
                "Value",
                value=str(value),
                key=__make_widget_key(editor_key, node, "string"),
                label_visibility="collapsed"
            )

def __render_data_node(
    editor_key: str,
    node: Node,
    editor_context: dict,
    node_key: str | int
) -> None:

    if node.is_object:
        __render_data_object(
            editor_key,
            node,
            editor_context,
            node_key
        )

    elif node.is_array:
        __render_data_array(
            editor_key,
            node,
            editor_context,
            node_key
        )

    else:
        __render_data_scalar(
            editor_key,
            node,
            node_key
        )

@st.fragment
def data_editor(
    data: dict | list | Node,
    key: str,
    context: dict[str, Any],
    expanded: bool | None = None,
    width: Literal["stretch", "content"] | int = "stretch",
    expand_all_label: str | None = None,
    collapse_all_label: str | None = None,
    is_one_based_array_index: bool | None = None
) -> Node:
    """
    Data-only editor version of the structure_editor.

    The structure nor data type of each element's value cannot be altered,
    can only be edited.

    Returns the root Node from the data with current editing.
    User can fetch data back using Node.data() method.

    In case when expand_all_label or collapse_all_label are provided,
    top level node will contain expand all or collapse all buttons respectively.

    data: root dict, list or Node. In case of Node, editor will be refreshed if the value changes (so user can set the editor by a new Node while it's opened)

    key: unique identifier for this editor instance.

    context: a dict for a data, so user can delete context[key] if needed
    to clear the structure_editor contextual data

    returns: a Node object with current data state that was created
    at context instantiation. This object also placed in context[key]["node"]
    """

    if key not in context:
        if isinstance(data, (dict, list)):
            data = Node.create(data)

        elif isinstance(data, Node):
            if not (data.is_object or data.is_array):
                raise TypeError(
                    "data Node must be an object or an array node as the root"
                )

        else:
            raise TypeError(
                f"data must be dict, list or appropriate Node as the root, "
                f"got {type(data)}"
            )

        context[key] = {
            "node": data,
            "default_expanded": bool(expanded),
            "expanded": {},
            "array_index_adjustment": 1 if is_one_based_array_index else 0
        }

    editor_context = context[key]
    root: Node = editor_context["node"]

    if isinstance(data, Node) and data != root:
        root = data
        editor_context["node"] = data

    with st.container(border=True, width=width):
        if expand_all_label or collapse_all_label:
            with st.container(horizontal=True):

                if expand_all_label and st.button(
                    expand_all_label,
                    icon=":material/expand_all:",
                    key=__make_widget_key(key, root, "expand_all")
                ):
                    editor_context["default_expanded"] = True
                    editor_context["expanded"].clear()
                    st.rerun(scope="fragment")

                if collapse_all_label and st.button(
                    collapse_all_label,
                    icon=":material/collapse_all:",
                    key=__make_widget_key(key, root, "collapse_all")
                ):
                    editor_context["default_expanded"] = False
                    editor_context["expanded"].clear()
                    st.rerun(scope="fragment")

        if root.is_object:
            for field, child in root.value.items():
                __render_data_node(
                    key, child, editor_context, field
                )

        elif root.is_array:
            for index, child in enumerate(root.value):
                __render_data_node(
                    key, child, editor_context, index
                )

    return root