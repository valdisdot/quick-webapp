from __future__ import annotations

from typing import Any
from collections.abc import Callable
import streamlit as st

class PageContext:
    """
    Simple helper class to hold page related data and state.

    In one word, provides an encapsulation and code shortcuts to work with state dictionaries.
    """

    def __init__(
            self,
            key: str,
            contexts: dict[str, dict[Any, Any]] | None = None,
            default_context: dict[Any, Any] | None = None,
            notification_duration_seconds: int = 2
        ):
        self.__key = key
        self.__contexts = {}
        self.__default_context = {}
        self.__notifications = []
        self.__notification_duration_seconds = int(notification_duration_seconds)

        if default_context and isinstance(default_context, dict):
            self.__default_context.update(default_context)

        if contexts and isinstance(contexts, dict):
            for key, item in contexts.items():
                if item is not None and isinstance(item, dict):
                    self.__contexts[key] = {item}

    @property
    def key(self) -> str:
        """
        Returns a data key of the page.
        """

        return self.__key

    def make_subkey(self, suffix: str) -> str:
        """
        Shortcut for PageData.key + "_" + suffix
        """

        return f"{self.__key}_{suffix}"

    def get_context(self, name: str | None = None) -> dict[Any, Any]:
        """
        Returns a context by its name or a default one.
        """

        return self.__contexts.get(name, self.__default_context)

    def put_notification(self, message: str, message_icon: str | None = None, pre_notification_action: Callable[[PageContext], Any] | None = None, post_notification_action: Callable[[PageContext], Any] | None = None):
        """
        Puts notification and its actions.

        Actions must accept the PageContext object (self)
        """

        self.__notifications.append((message, message_icon, pre_notification_action, post_notification_action))

    def fire_notifications(self):
        """
        Fires all notifications that was put with put_notification() 
        """

        while self.__notifications:
            message, message_icon, pre_notification_action, post_notification_action = self.__notifications.pop(0)

            if pre_notification_action and isinstance(pre_notification_action, Callable):
                pre_notification_action(self)

            st.toast(message, icon=message_icon, duration=self.__notification_duration_seconds)

            if post_notification_action and isinstance(post_notification_action, Callable):
                post_notification_action(self)

    def apply(self, action: Callable[[PageContext], Any]):
        """
        Apply an action to this PageContext (reversed setter)
        """

        if action and isinstance(action, Callable):
            action(self)