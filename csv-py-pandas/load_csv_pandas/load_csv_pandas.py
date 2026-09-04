"""Pandas CSV load workflow.

Purpose: read CSV rows as dictionaries or generated dataclass instances.
Usage: import and call ``load_csv``; see load_csv_pandas.md for an example.
Substeps: resolve and validate the path, read a pandas data frame, then return
dictionaries or dataclasses. See load_csv_pandas.md for details.
"""

import keyword
import re
from dataclasses import make_dataclass
from pathlib import Path

import pandas as pd

PathInput = str | Path
CsvRow = dict[str, str]
CsvTable = list[CsvRow]
LoadResult = CsvTable | list[object]


class CsvFileNotFoundError(FileNotFoundError):
    """Raised when the requested CSV input file does not exist."""


def resolve_csv_path(file_path: PathInput) -> Path:
    """Expand and resolve a CSV path."""
    return Path(file_path).expanduser().resolve()


def normalize_class_name(file_path: Path) -> str:
    """Create a valid dataclass name from the CSV filename."""
    parts = [part for part in re.split(r"\W+", file_path.stem) if part]
    class_name = "".join(part[:1].upper() + part[1:] for part in parts)
    if not class_name:
        return "CsvRow"
    if class_name[0].isdigit():
        class_name = f"Csv{class_name}"
    if keyword.iskeyword(class_name):
        class_name = f"{class_name}Row"
    return class_name


def normalize_field_name(name: str, used_names: dict[str, int]) -> str:
    """Create a unique valid Python field name from a CSV header."""
    field_name = re.sub(r"\W+", "_", name.strip()).strip("_") or "field"
    if field_name[0].isdigit():
        field_name = f"field_{field_name}"
    if keyword.iskeyword(field_name):
        field_name = f"{field_name}_"
    count = used_names.get(field_name, 0)
    used_names[field_name] = count + 1
    return f"{field_name}_{count + 1}" if count else field_name


def convert_rows_to_dataclasses(
    table: CsvTable, headers: list[str], class_name: str
) -> list[object]:
    """Convert dictionary rows to a generated dataclass type."""
    used_names: dict[str, int] = {}
    field_map = {normalize_field_name(header, used_names): header for header in headers}
    row_class = make_dataclass(
        class_name, [(field_name, str) for field_name in field_map]
    )
    return [
        row_class(
            **{field_name: row[header] for field_name, header in field_map.items()}
        )
        for row in table
    ]


def _read_csv_frame(file_path: Path, encoding: str) -> pd.DataFrame:
    try:
        return pd.read_csv(
            file_path,
            dtype=str,
            encoding=encoding,
            header=None,
            keep_default_na=False,
            na_filter=False,
        )
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _frame_to_table(frame: pd.DataFrame) -> tuple[CsvTable, list[str]]:
    if frame.empty:
        return [], []

    headers = [str(header) for header in frame.iloc[0].tolist()]
    data_frame = frame.iloc[1:].reset_index(drop=True)
    table = [
        {header: str(value) for header, value in zip(headers, row.tolist())}
        for _, row in data_frame.iterrows()
    ]

    return table, headers


def load_csv(
    file_path: PathInput, encoding: str = "utf-8-sig", as_dataclass: bool = True
) -> LoadResult:
    file_path = resolve_csv_path(file_path)

    if not file_path.is_file():
        raise CsvFileNotFoundError(f"{file_path} not found")

    table, headers = _frame_to_table(_read_csv_frame(file_path, encoding))

    if as_dataclass:
        return convert_rows_to_dataclasses(
            table, headers, class_name=normalize_class_name(file_path)
        )

    return table
