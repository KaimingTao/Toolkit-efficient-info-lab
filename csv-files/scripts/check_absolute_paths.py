"""Report hard-coded absolute path literals in Python source code."""

import ast
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
    violations = []
    for path in python_files(PROJECT_ROOT):
        for node in find_absolute_path_literals(path):
            relative_path = path.relative_to(PROJECT_ROOT)
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
