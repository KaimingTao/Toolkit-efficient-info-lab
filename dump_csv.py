"""CSV dumping entry point.

Design requirements:
- Accept either a string path or a pathlib.Path object.
- Convert the input path to a resolved pathlib.Path before validation or I/O.
- Expand user home markers such as "~" during path normalization.
- Create missing parent directories before writing.
- Accept a table as a list of dictionaries or dataclass instances.
- Do not validate cell values by default.
- Warn when asked to dump an empty table.
- Allow the header argument to be omitted.
- Infer CSV headers from row keys or dataclass fields when no header is provided.
- Preserve inferred header order by first occurrence while scanning rows.
- Write CSV records with csv.DictWriter using UTF-8 with BOM support.
- Always write the CSV header row before data rows.
"""

import csv
import warnings
from dataclasses import asdict
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

PathInput = Union[str, Path]
CsvRow = Dict[str, Any]
CsvTable = List[CsvRow]
TableRow = Union[CsvRow, Any]


def resolve_csv_path(file_path: PathInput) -> Path:
    return Path(file_path).expanduser().resolve()


def row_to_dict(row: TableRow) -> CsvRow:
    if is_dataclass(row) and not isinstance(row, type):
        return asdict(row)
    return row


def normalize_table(table: Iterable[TableRow]) -> CsvTable:
    return [row_to_dict(row) for row in table]


def infer_header(table: CsvTable) -> List[str]:
    header = []

    for row in table:
        for key in row:
            if key not in header:
                header.append(key)

    return header


def dump_csv(
    file_path: PathInput,
    table: Iterable[TableRow],
    header: Optional[Sequence[str]] = None,
    encoding: str = "utf-8-sig",
) -> None:
    file_path = resolve_csv_path(file_path)
    file_path.parent.mkdir(exist_ok=True, parents=True)

    rows = normalize_table(table)
    if not rows:
        warnings.warn(f"{file_path} table is empty.")

    fieldnames = list(header) if header is not None else infer_header(rows)

    with file_path.open("w", encoding=encoding, newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
