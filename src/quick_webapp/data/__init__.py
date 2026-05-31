from collections.abc import Callable
import streamlit as st
from quick_webapp.service.shutdown_hook import ShutdownHookHolder
from quick_webapp.data.environment import Environment
from quick_webapp.data.persistent_state import PersistentState
from quick_webapp.data.temporary_storage import TemporaryStorage

@st.cache_resource
def ensure_environment(environment_path: str = "environment.env") -> Environment:
    """
    повертає об'єкт оточення Environment, який живе в глобальному контексті
    """

    return Environment(environment_path)

@st.cache_resource
def ensure_persistent_state(persistent_state_key: str, _shutdown_hook_holder: ShutdownHookHolder, _persistent_state_supplier: Callable[[], PersistentState] | None = None) -> PersistentState:
    """
    повертає об'єкт стану State, який живе в глобальному контексті
    """

    persistent_state: PersistentState = None

    if _persistent_state_supplier is not None and isinstance(_persistent_state_supplier, Callable):
        persistent_state = _persistent_state_supplier()
        if persistent_state is None or not isinstance(persistent_state, PersistentState):
            persistent_state = PersistentState(persistent_state_key, False, False)
        else:
            _shutdown_hook_holder.add_hook(lambda: persistent_state.persist_state())
    else:
        persistent_state = PersistentState(persistent_state_key, False, False)
    
    return persistent_state

@st.cache_resource
def ensure_temporary_storage(temporary_storage_key: str, _shutdown_hook_holder: ShutdownHookHolder) -> TemporaryStorage:
    """
    повертає об'єкт сховища тимчасових файлів TemporaryStorage, який живе в глобальному контексті
    """

    temporary_storage = TemporaryStorage()
    _shutdown_hook_holder.add_hook(lambda: temporary_storage.clear())
    return temporary_storage