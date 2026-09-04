"""Generate workflow UPDATE.md files from Git history.

Purpose: create empty update-date markers for each step folder.
Usage: uv run python generate_update_files/generate_update_files.py
Substeps: discover documented workflow folders, query Git dates, then write
updated_at_YYYY-MM-DD.md files. See generate_update_files.md for details.
"""

import subprocess
from datetime import UTC, datetime
from pathlib import Path

SOURCE_SUFFIXES = {".py", ".rs", ".js", ".html"}


def run_git(*arguments: str) -> str:
    """Run Git in the repository root and return decoded standard output."""
    return subprocess.run(
        ["git", *arguments], check=True, capture_output=True, text=True
    ).stdout.strip()


def step_folders(repository_root: Path) -> set[Path]:
    """Find folders with a source entry file and its same-named document."""
    tracked_paths = [Path(path) for path in run_git("ls-files").splitlines()]
    folders = set()
    for path in tracked_paths:
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        for folder in (path.parent, *path.parents):
            if repository_root.joinpath(folder, f"{path.stem}.md").is_file():
                folders.add(repository_root / folder)
                break
            if folder == Path("."):
                break
    return folders


def latest_update_date(repository_root: Path, folder: Path) -> str:
    """Return the latest Git commit date for tracked files below a step folder."""
    relative_folder = folder.relative_to(repository_root)
    return run_git("log", "-1", "--format=%cs", "--", str(relative_folder))


def staged_paths() -> set[Path]:
    """Return repository-relative files staged for the pending commit."""
    return {
        Path(path) for path in run_git("diff", "--cached", "--name-only").splitlines()
    }


def main() -> None:
    """Write an empty date-named update marker for every workflow folder."""
    repository_root = Path(run_git("rev-parse", "--show-toplevel"))
    staged = staged_paths()
    for folder in sorted(step_folders(repository_root)):
        relative_folder = folder.relative_to(repository_root)
        update_date = (
            datetime.now(UTC).date().isoformat()
            if any(path.is_relative_to(relative_folder) for path in staged)
            else latest_update_date(repository_root, folder)
        )
        for previous_marker in folder.glob("updated_at_*.md"):
            previous_marker.unlink()
        (folder / f"updated_at_{update_date}.md").touch()


if __name__ == "__main__":
    main()
