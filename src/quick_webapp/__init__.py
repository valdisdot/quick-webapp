from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, overload, cast
import streamlit as st

T = TypeVar("T")
DecoratorT = Callable[[Callable[[], T]], Callable[[], T]]

@st.cache_resource(scope="session")
def ensure_session_object(
    session_object_key: str,
    _session_object_supplier: Callable[[], Any] | None = None,
) -> Any:
    """
    Returns an object that lives in the current Streamlit session.

    If ``_session_object_supplier`` is provided and is callable, it is used
    to create the object. Otherwise, an empty dictionary is returned.
    """

    if _session_object_supplier is not None and isinstance(_session_object_supplier, Callable):
        return _session_object_supplier()
    return {}

@st.cache_resource
def ensure_object(
    object_key: str,
    _object_supplier: Callable[[], Any] | None = None,
) -> Any:
    """
    Returns an object that lives in the global (cached) context.

    If ``_object_supplier`` is provided and is callable, it is used
    to create the object. Otherwise, an empty dictionary is returned.
    """

    if _object_supplier is not None and isinstance(_object_supplier, Callable):
        return _object_supplier()
    return {}


@overload
def session_bean(__func: Callable[[], T], /) -> Callable[[], T]: ...

@overload
def session_bean(*, key: str | None = None) -> DecoratorT[T]: ...

def session_bean(
    __func: Callable[[], T] | None = None,
    /,
    *,
    key: str | None = None,
) -> Callable[[], T] | DecoratorT[T]:
    """
    Returns the returned object of the wrapped function that lives in the current Streamlit session.

    Usable as:
      @session_bean
      def f() -> T: ...

    or:
      @session_bean(key="some_key")
      def f() -> T: ...
    """

    def decorator(factory: Callable[[], T]) -> Callable[[], T]:
        a_key = factory.__name__ if key is None else key

        @wraps(factory)
        def wrapper() -> T:
            return cast(T, ensure_session_object(a_key, factory))

        return wrapper

    if __func is not None:
        return decorator(__func)

    return decorator

@overload
def bean(__func: Callable[[], T], /) -> Callable[[], T]: ...

@overload
def bean(*, key: str | None = None) -> DecoratorT[T]: ...

def bean(
    __func: Callable[[], T] | None = None,
    /,
    *,
    key: str | None = None,
) -> Callable[[], T] | DecoratorT[T]:
    """
    Returns the returned object of the wrapped function that lives in the global (cached) context.

    Usable as:
      @bean
      def f() -> T: ...

    or:
      @bean(key="some_key")
      def f() -> T: ...
    """

    def decorator(factory: Callable[[], T]) -> Callable[[], T]:
        a_key = factory.__name__ if key is None else key

        @wraps(factory)
        def wrapper() -> T:
            return cast(T, ensure_object(a_key, factory))

        return wrapper

    if __func is not None:
        return decorator(__func)
    return decorator

def clear():
    """
    Clears all context so next factory methods recreate their object.
    """

    st.cache_resource.clear()