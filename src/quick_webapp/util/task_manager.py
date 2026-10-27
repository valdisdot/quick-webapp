from concurrent.futures import ThreadPoolExecutor, Future
from collections.abc import Callable
from typing import Any
import threading
import time

class TaskManager:
    """
    Wrapper around an ExecutorService with a task counter.
    """

    def __init__(self, thread_name_prefix):
        self.__tasks: dict[int, Future] = {}
        self.__lock = threading.Lock()
        self.__executor = ThreadPoolExecutor(thread_name_prefix=thread_name_prefix)

    @staticmethod
    def __schedule(callable_: Callable[[], Any], attempts: int, sleep_interval: float) -> Any:
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

    def schedule(self, callable_: Callable[[], Any], attempts: int = 1, sleep_interval: float = 1.0) -> int:
        """
        Creates a task that calls the given callable up to 'attempts' times
        with a delay of 'sleep_interval' seconds between attempts.

        The callable should return a non-None value to stop retrying,
        otherwise it will be called 'attempts' times.

        To interrupt early from inside, the callable should raise an exception.

        If attempts=0, the task will not be scheduled.
        If sleep_interval=0, there will be no delay between attempts.
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
        Checks if the task with the given task_id has completed.
        """

        with self.__lock:
            future = self.__tasks.get(task_id)

        return future is None or future.done()

    def result(self, task_id: int) -> Any:
        """
        Returns the result of the task or raises an exception.

        CancelledError - if the task was cancelled
        TimeoutError - if a timeout is used
        Other exceptions - any exception raised by the callable
        """

        with self.__lock:
            future = self.__tasks.get(task_id)

        if future is None:
            return None

        return future.result()

    def cancel(self, task_id: int) -> bool:
        """
        Cancels the task with the given task_id.

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