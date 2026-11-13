from __future__ import annotations

from typing import Any, TypeVar, overload, cast
from collections.abc import Callable
from functools import lru_cache, wraps
from threading import RLock
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

__object_suppliers: dict[str, Callable[[], Any] | None] = {}
__object_suppliers_lock = RLock()

@lru_cache(maxsize=None)
def __get_object(object_key: str) -> Any:
    return __object_suppliers.get(object_key)()

def ensure_object(
    object_key: str,
    _object_supplier: Callable[[], Any] | None = None,
) -> Any:
    """
    Returns a globally cached singleton associated with object_key.

    The first supplier registered for a key wins.
    Independent of Streamlit runtime.
    """

    with __object_suppliers_lock:
        if object_key not in __object_suppliers:
            __object_suppliers[object_key] = _object_supplier if _object_supplier and callable(_object_supplier) else lambda: {}
    
    return __get_object(object_key)

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

def clear_sessions_objects():
    """
    Clears Streamlit session context.
    """

    st.cache_resource.clear()

def clear_objects() -> None:
    """
    Clears global objects and their suppliers.
    """

    with __object_suppliers_lock:
        __object_suppliers.clear()
        __get_object.cache_clear()

def clear():
    """
    Clears all context (session and global) so next factory methods recreate their object.
    """

    clear_sessions_objects()
    clear_objects()