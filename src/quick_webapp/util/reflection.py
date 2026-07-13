from pathlib import Path
from typing import Any
import ast

from quick_webapp.util.commons import get_file_paths


def _ast_to_value(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return ast.unparse(node)


def scan_params(
    function_name: str,
    package_root: str | Path | None,
    *package_path: str
) -> dict[Path, list[dict[str, Any]]]:
    """
    Returns a dictionary with Path: list pair where list contains dictionaries with 2 items: args and kwargs

    - args contains all position args
    - kwargs contains all named args

    If list is empty then no function_name calls were found.

    """

    result: dict[Path, list[dict[str, Any]]] = {}

    for path_str in get_file_paths(package_root, "py", *package_path):
        path = Path(path_str)
        tree = ast.parse(path.read_text())

        calls: list[dict[str, Any]] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            matches = (
                isinstance(node.func, ast.Name)
                and node.func.id == function_name
            ) or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == function_name
            )

            if not matches:
                continue

            calls.append({
                "args": [_ast_to_value(arg) for arg in node.args],
                "kwargs": {
                    kw.arg: _ast_to_value(kw.value)
                    for kw in node.keywords
                },
            })

        result[path] = calls

    return result