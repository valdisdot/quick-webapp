
from typing import Any
from collections.abc import Callable
from functools import wraps
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


def session_bean(key: str | None = None):
    """
    Return the returned object of the wrapped function that lives in the current Streamlit session.
    """

    def decorator(factory):
        a_key = factory.__name__ if key is None else key

        @wraps(factory)
        def wrapper():
            return ensure_session_object(a_key, factory)

        return wrapper

    if callable(key):
        factory = key
        key = None
        return decorator(factory)

    return decorator


def bean(key: str | None = None):
    """
    Return the returned object of the wrapped function that lives in the global (cached) context.
    """

    def decorator(factory):
        a_key = factory.__name__ if key is None else key

        @wraps(factory)
        def wrapper():
            return ensure_object(a_key, factory)

        return wrapper

    if callable(key):
        factory = key
        key = None
        return decorator(factory)

    return decorator


@session_bean(st.context.url)
def page_session_bean() -> dict[Any, Any]:
    """
    Return a current page object (url based) that lives in the current Streamlit session.

    """

    return {}