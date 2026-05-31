
from typing import Any
from collections.abc import Callable
import streamlit as st


@st.cache_resource(scope="session")
def ensure_session_object(
    session_object_key: str,
    _session_object_supplier: Callable[[], Any] | None = None,
) -> Any:
    """
    Return an object that lives in the current Streamlit session.

    If ``_session_object_supplier`` is provided and is callable, it is used
    to create the object. Otherwise, an empty dictionary is returned.
    """

    if _session_object_supplier is not None and isinstance(_session_object_supplier, Callable):
        return _session_object_supplier()
    else:
        return {}


@st.cache_resource
def ensure_object(
    object_key: str,
    _object_supplier: Callable[[], Any] | None = None,
) -> Any:
    """
    Return an object that lives in the global (cached) context.

    If ``_object_supplier`` is provided and is callable, it is used
    to create the object. Otherwise, an empty dictionary is returned.
    """

    if _object_supplier is not None and isinstance(_object_supplier, Callable):
        return _object_supplier()
    else:
        return {}