"""Dump CSV workflow.

Purpose: write dictionaries or dataclass instances to a CSV file.
Usage: import and call ``dump_csv``; see dump_csv.md for an example.
Substeps: resolve the output path, normalize rows and headers, then write the
header and CRLF-terminated records with ``csv.DictWriter``. See dump_csv.md
for details.
"""

import csv
import warnings
from collections.abc import Iterable, Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

PathInput = str | Path
CsvRow = dict[str, Any]
CsvTable = list[CsvRow]
TableRow = CsvRow | Any


def resolve_csv_path(file_path: PathInput) -> Path:
    return Path(file_path).expanduser().resolve()


def row_to_dict(row: TableRow) -> CsvRow:
    if is_dataclass(row) and not isinstance(row, type):
        return asdict(row)
    return row


def normalize_table(table: Iterable[TableRow]) -> CsvTable:
    return [row_to_dict(row) for row in table]


def infer_header(table: CsvTable) -> list[str]:
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
    file_path = resolve_csv_path(file_path)
    file_path.parent.mkdir(exist_ok=True, parents=True)

    rows = normalize_table(table)
    if not rows:
        warnings.warn(f"{file_path} table is empty.")

    fieldnames = list(header) if header is not None else infer_header(rows)

    with file_path.open("w", encoding=encoding, newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)
