from concurrent.futures import ThreadPoolExecutor, Future
from collections.abc import Callable
from typing import Any
import threading
import time


class TaskManager:
    """
    Wrapper aka ExecutorService with a counter.
    """

    def __init__(self):
        self.__tasks: dict[int, Future] = {}
        self.__lock = threading.Lock()
        self.__executor = ThreadPoolExecutor()

    @staticmethod
    def __schedule(
        callable_: Callable[[], Any],
        attempts: int,
        sleep_interval: float
    ) -> Any:
        counter = 0

        while True:
            counter += 1

            result = callable_()

            if result is not None:
                return result

            if attempts > counter:
                if sleep_interval > 0:
                    time.sleep(sleep_interval)
            else:
                return result

    def schedule(
        self,
        callable_: Callable[[], Any],
        attempts: int = 1,
        sleep_interval: float = 1.0
    ) -> int:
        """
        Creates a task that calls callable() up to `attempts` times,
        with an interval of `sleep_interval` between attempts.

        callable must return a non-None value,
        otherwise it will be executed `attempts` times.

        To interrupt the task early from within callable,
        callable must raise an exception.

        If attempts=0, the task will not be scheduled.
        If sleep_interval=0, there will be no delay.
        """

        if callable_ is None or not callable(callable_):
            raise ValueError("callable is not a function nor method")

        if attempts < 0:
            raise ValueError("attempts is negative")

        if sleep_interval < 0:
            raise ValueError("sleep_interval is negative")

        task_id = time.time_ns()

        if attempts:
            future = self.__executor.submit(
                self.__schedule,
                callable_,
                attempts,
                sleep_interval
)
            with self.__lock:
                self.__tasks[task_id] = future

        return task_id

    def is_completed(self, task_id: int) -> bool:
        """
        Checks whether the task has completed.
        """

        with self.__lock:
            future = self.__tasks.get(task_id)

        return future is None or future.done()

    def result(self, task_id: int) -> Any:
        """
        Returns the task result or raises an exception.

        CancelledError - the task was cancelled.
        TimeoutError - if a timeout is specified.
        Any other exception - an exception raised by callable().
        """

        with self.__lock:
            future = self.__tasks.get(task_id)

        if future is None:
            return None

        return future.result()

    def cancel(self, task_id: int) -> bool:
        """
        Cancels the task.

        Returns True if the task was successfully cancelled.
        """

        with self.__lock:
            future = self.__tasks.get(task_id)

        if future and not future.done():
            return future.cancel()

        return False

    def throw_away(self, task_id: int):
        """
        Removes the task from the task list.
        """

        with self.__lock:
            future = self.__tasks.get(task_id)

            if future:
                if not future.done():
                    future.cancel()

                del self.__tasks[task_id]
    
    def shutdown_now(self):
        """
        Shuts down the executor and cancels all unfinished tasks.
        """

        self.__executor.shutdown(wait=False, cancel_futures=True)