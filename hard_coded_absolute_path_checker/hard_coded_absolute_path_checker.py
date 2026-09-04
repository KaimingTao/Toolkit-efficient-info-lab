"""Hard-Coded Absolute Path Checker workflow.

Purpose: report hard-coded absolute path literals in Python files below a
specified folder. Usage: uv run python
hard_coded_absolute_path_checker/hard_coded_absolute_path_checker.py <folder-path>
Substeps: validate the folder, discover Python files, inspect string literals
with the AST, then report violations and exit nonzero when any are found. See
hard_coded_absolute_path_checker.md for the complete workflow document.
"""

import argparse
import ast
import re
import sys
from pathlib import Path

SKIPPED_DIRECTORIES = {".git", ".venv", "__pycache__"}
WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")


def is_absolute_path_literal(value: str) -> bool:
    """Return whether a string literal is an absolute POSIX or Windows path."""
    return Path(value).is_absolute() or bool(WINDOWS_ABSOLUTE_PATH.match(value))


def python_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*.py")
        if not any(part in SKIPPED_DIRECTORIES for part in path.relative_to(root).parts)
    ]


def find_absolute_path_literals(path: Path) -> list[ast.Constant]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path)
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and is_absolute_path_literal(node.value)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report hard-coded absolute path literals in Python source files."
    )
    parser.add_argument(
        "folder_path",
        type=Path,
        help="Folder containing Python files to check.",
    )
    arguments = parser.parse_args()
    folder_path = arguments.folder_path.expanduser().resolve()
    if not folder_path.is_dir():
        parser.error(f"folder path is not a directory: {folder_path}")

    violations = []
    for path in python_files(folder_path):
        for node in find_absolute_path_literals(path):
            relative_path = path.relative_to(folder_path)
            violations.append(
                f"{relative_path}:{node.lineno}:{node.col_offset + 1}: "
                f"absolute path literal {node.value!r}"
            )

    if violations:
        print("Absolute path literals found:", file=sys.stderr)
        print("\n".join(violations), file=sys.stderr)
        return 1

    print("No hard-coded absolute paths found in Python source files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
