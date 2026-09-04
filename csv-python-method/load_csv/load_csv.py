"""Load CSV workflow.

Purpose: read a CSV file as dictionaries or generated dataclass instances.
Usage: import and call ``load_csv``; see load_csv.md for an example.
Substeps: resolve the input path, detect the CSV file, BOM, and line breaks,
read records with ``csv.DictReader`` while preserving CSV line endings, then
optionally convert rows to dataclasses. See
load_csv.md for details.
"""

import csv
import keyword
import re
import uuid
from dataclasses import dataclass, make_dataclass
from pathlib import Path
from typing import Any

PathInput = str | Path
CsvValue = str | list[str] | None
CsvRow = dict[str | None, CsvValue]
CsvTable = list[CsvRow]
DataclassTable = list[Any]
LoadResult = CsvTable | DataclassTable
UTF_BOMS = (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")


class CsvFileNotFoundError(FileNotFoundError):
    """Raised when the requested CSV input file does not exist."""


class CsvFileTypeError(ValueError):
    """Raised when the requested input does not have a CSV file extension."""


@dataclass(frozen=True)
class CsvFileFormat:
    """Detected byte-order-mark and line-break details for a CSV file."""

    has_bom: bool
    line_break: str | None


def resolve_csv_path(file_path: PathInput) -> Path:
    return Path(file_path).expanduser().resolve()


def detect_csv_file(file_path: Path) -> None:
    """Validate that the input is an existing regular file with a CSV extension."""
    if not file_path.is_file():
        raise CsvFileNotFoundError(f"{file_path} not found")
    if file_path.suffix.lower() != ".csv":
        raise CsvFileTypeError(f"{file_path} does not have a .csv extension")


def detect_csv_file_format(file_path: Path) -> CsvFileFormat:
    """Detect whether a CSV has a BOM and which line-break style it uses."""
    contents = file_path.read_bytes()
    remaining_contents = contents.replace(b"\r\n", b"")
    line_breaks = []

    if b"\r\n" in contents:
        line_breaks.append("\r\n")
    if b"\n" in remaining_contents:
        line_breaks.append("\n")
    if b"\r" in remaining_contents:
        line_breaks.append("\r")

    if len(line_breaks) > 1:
        line_break = "mixed"
    elif line_breaks:
        line_break = line_breaks[0]
    else:
        line_break = None

    return CsvFileFormat(
        has_bom=contents.startswith(UTF_BOMS),
        line_break=line_break,
    )


def normalize_class_name(file_path: Path) -> str:
    parts = [part for part in re.split(r"\W+", file_path.stem) if part]
    class_name = "".join(part[:1].upper() + part[1:] for part in parts)

    if not class_name:
        class_name = "CsvRow"
    if class_name[0].isdigit():
        class_name = f"Csv{class_name}"
    if keyword.iskeyword(class_name):
        class_name = f"{class_name}Row"

    return class_name


def normalize_field_name(name: str | None, used_names: dict[str, int]) -> str:
    if name is None:
        field_name = f"field_{uuid.uuid4().hex}"
    else:
        field_name = str(name).strip()

    field_name = re.sub(r"\W+", "_", field_name)
    field_name = field_name.strip("_")

    if not field_name:
        field_name = "field"
    if field_name[0].isdigit():
        field_name = f"field_{field_name}"
    if keyword.iskeyword(field_name):
        field_name = f"{field_name}_"

    count = used_names.get(field_name, 0)
    used_names[field_name] = count + 1

    if count:
        return f"{field_name}_{count + 1}"
    return field_name


def build_field_map(headers: list[str | None]) -> dict[str, str | None]:
    used_names: dict[str, int] = {}
    return {normalize_field_name(header, used_names): header for header in headers}


def convert_rows_to_dataclasses(
    table: CsvTable, headers: list[str | None], class_name: str = "CsvRow"
) -> DataclassTable:
    field_map = build_field_map(headers)
    row_class = make_dataclass(
        class_name,
        [(field_name, CsvValue) for field_name in field_map],
        namespace={"__csv_field_map__": field_map},
    )

    return [
        row_class(
            **{field_name: row.get(header) for field_name, header in field_map.items()}
        )
        for row in table
    ]


def load_csv(
    file_path: PathInput, encoding: str = "utf-8-sig", as_dataclass: bool = True
) -> LoadResult:
    file_path = resolve_csv_path(file_path)
    detect_csv_file(file_path)
    detect_csv_file_format(file_path)

    with file_path.open(encoding=encoding, newline="") as fd:
        reader = csv.DictReader(fd)
        table = list(reader)
        headers = reader.fieldnames or []

    if as_dataclass:
        return convert_rows_to_dataclasses(
            table, headers, class_name=normalize_class_name(file_path)
        )

    return table
