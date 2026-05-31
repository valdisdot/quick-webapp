from typing import Any
from collections.abc import Callable

def include_value(key: str, source: dict[str, Any], mapping_key: str, target: dict[str, Any], value_mapper: None | Callable[[Any], Any] = None):
    """
    Includes the value by `key` from `source` into `target` under `mapping_key` only if the value exists and is not None,
    converting the value via `value_mapper` if it is provided.
    """

    value = source.get(key, None)
    if value is not None:
        target[mapping_key] = value_mapper(value) if value_mapper else value