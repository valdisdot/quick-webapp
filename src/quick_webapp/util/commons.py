from typing import Any
from collections.abc import Callable
import inspect
import os
from pathlib import Path

def include_value(key: str, source: dict[str, Any], mapping_key: str, target: dict[str, Any], value_mapper: None | Callable[[Any], Any] = None):
    """
    Includes the value by `key` from `source` into `target` under `mapping_key` only if the value exists and is not None,
    converting the value via `value_mapper` if it is provided.
    """

    value = source.get(key, None)
    if value is not None:
        target[mapping_key] = value_mapper(value) if value_mapper else value

def get_file_paths(root: str | Path | None, extension: str | None, *path_nodes: str) -> list[Path]:
    """
    Returns all files from the root directory by a specified path elements with the extension. 
    If root is no specified - caller parent directory is used.
    If extension is not specified, all '*' files return.
    If path_nodes is absent, looks up in the root.
    """

    root = Path(inspect.stack()[1].filename).resolve().parent if root is None else (root.resolve() if isinstance(root, Path) else Path(root).resolve())
    search_dir = root.joinpath(*path_nodes) if path_nodes else root

    return sorted(
        path
        for path in search_dir.rglob(f"*.{extension}" if extension is not None else "*")
        if path.is_file()
    )