"""Pandas CSV dump workflow.

Purpose: write dictionary or dataclass rows to a CRLF-terminated CSV file.
Usage: import and call ``dump_csv``; see dump_csv_pandas.md for an example.
Substeps: resolve the path, normalize rows and headers, then write records with
pandas. See dump_csv_pandas.md for dependencies and security details.
"""

import warnings
from collections.abc import Iterable, Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import pandas as pd

PathInput = str | Path
CsvRow = dict[str, Any]
TableRow = CsvRow | Any


def row_to_dict(row: TableRow) -> CsvRow:
    """Convert a dataclass row to a dictionary when necessary."""
    if is_dataclass(row) and not isinstance(row, type):
        return asdict(row)
    return row


def normalize_table(table: Iterable[TableRow]) -> list[CsvRow]:
    """Convert all supported table rows to dictionaries."""
    return [row_to_dict(row) for row in table]


def infer_header(table: list[CsvRow]) -> list[str]:
    """Infer header order from the first occurrence of each row key."""
    header = []
    for row in table:
        for key in row:
            if key not in header:
                header.append(key)
    return header


def dump_csv(
    file_path: PathInput,
    table: Iterable[TableRow],
    header: Sequence[str] | None = None,
    encoding: str = "utf-8-sig",
) -> None:
    file_path = Path(file_path).expanduser().resolve()
    file_path.parent.mkdir(exist_ok=True, parents=True)

    rows = normalize_table(table)
    if not rows:
        warnings.warn(f"{file_path} table is empty.")

    fieldnames = list(header) if header is not None else infer_header(rows)
    frame = pd.DataFrame(rows, columns=fieldnames)
    frame = frame.fillna("").astype(str)
    frame.to_csv(file_path, index=False, encoding=encoding, lineterminator="\r\n")
