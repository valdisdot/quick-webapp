from typing import Any
from collections.abc import Callable

class ShutdownHookHolder:
    """
    Wrapper structure for invoking actions during application shutdown.
    """

    def __init__(self):
        self.__holder = []

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
            except Exception as e:
                print(f"Got an error with a shutdown hook: {e}")
