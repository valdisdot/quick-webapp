import streamlit as st
from quick_webapp.service.shutdown_hook import ShutdownHookHolder
from quick_webapp.service.task_manager import TaskManager

@st.cache_resource  
def ensure_shutdown_hook_holder(shutdown_hook_holder_key: str) -> ShutdownHookHolder:
    """
    повертає об'єкт задач перед закриттям ShutdownHookHolder, який живе в глобальному контексті
    """

    return ShutdownHookHolder(shutdown_hook_holder_key)

@st.cache_resource
def ensure_task_manager(task_manager_key: str, _shutdown_hook_holder: ShutdownHookHolder) -> TaskManager:
    """
    повертає об'єкт фонових задач TaskManager, який живе в глобальному контексті
    """

    task_manager = TaskManager(task_manager_key)
    _shutdown_hook_holder.add_hook(lambda: task_manager.shutdown_now())
    return task_manager