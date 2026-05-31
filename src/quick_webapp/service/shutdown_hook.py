from typing import Any
from collections.abc import Callable
import logging
import atexit

class ShutdownHookHolder:
    """
    Wrapper structure for invoking actions during application shutdown.
    """

    def __init__(self, hook_logger_name: str):
        self.__holder = []
        self.__logger = logging.getLogger(hook_logger_name)
        atexit.register(self.terminate)

    def add_hook(self, callable: Callable[[], Any]):
        """
        Adds an action to the wrapper.
        """

        self.__holder.append(callable)
    
    def terminate(self):
        """
        Executes all registered actions and removes them from the structure.
        """

        while len(self.__holder):
            try:
                self.__holder.pop()()
            except Exception:
                self.__logger.exception("An exeption occured during shutdown hook execution")
