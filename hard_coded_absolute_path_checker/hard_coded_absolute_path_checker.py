"""Hard-Coded Absolute Path Checker workflow.

Purpose: report hard-coded absolute paths in all non-gitignored text files
below a specified folder. Usage: uv run python
hard_coded_absolute_path_checker/hard_coded_absolute_path_checker.py <folder-path>
Substeps: validate the folder, discover non-gitignored files, inspect readable
text for absolute paths, then report violations and exit nonzero when any are found. See
hard_coded_absolute_path_checker.md for the complete workflow document.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

WINDOWS_ABSOLUTE_PATH = re.compile(r'(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\s"\']*')
POSIX_ABSOLUTE_PATH = re.compile(r'(?<![:A-Za-z0-9_/])/(?!/)[^\s"\']+')


def unignored_files(root: Path) -> list[Path]:
    """Return Git-tracked or unignored files beneath the requested folder."""
    repository_root = Path(
        subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        check=True,
        capture_output=True,
    )
    return [
        repository_root / relative_path
        for relative_path in result.stdout.decode().split("\0")
        if relative_path and (repository_root / relative_path).is_relative_to(root)
    ]


def find_absolute_paths(path: Path) -> list[tuple[int, int, str]]:
    """Return absolute-path matches from a readable text file, skipping binary data."""
    contents = path.read_bytes()
    if b"\0" in contents:
        return []
    matches = []
    for line_number, line in enumerate(
        contents.decode("utf-8", errors="ignore").splitlines(), 1
    ):
        for pattern in (WINDOWS_ABSOLUTE_PATH, POSIX_ABSOLUTE_PATH):
            matches.extend(
                (line_number, match.start() + 1, match.group())
                for match in pattern.finditer(line)
            )
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report hard-coded absolute paths in non-gitignored text files."
    )
    parser.add_argument(
        "folder_path",
        type=Path,
        help="Folder containing non-gitignored files to check.",
    )
    arguments = parser.parse_args()
    folder_path = arguments.folder_path.expanduser().resolve()
    if not folder_path.is_dir():
        parser.error(f"folder path is not a directory: {folder_path}")

    violations = []
    for path in unignored_files(folder_path):
        for line, column, value in find_absolute_paths(path):
            relative_path = path.relative_to(folder_path)
            violations.append(
                f"{relative_path}:{line}:{column}: absolute path {value!r}"
            )

    if violations:
        print("Absolute path literals found:", file=sys.stderr)
        print("\n".join(violations), file=sys.stderr)
        return 1

    print("No hard-coded absolute paths found in non-gitignored text files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
