"""CSV loading entry point.

Design requirements:
- Accept either a string path or a pathlib.Path object.
- Convert the input path to a resolved pathlib.Path before validation or I/O.
- Expand user home markers such as "~" during path normalization.
- Raise an exception when the resolved file path does not exist.
- Read CSV records with csv.DictReader using UTF-8 with BOM support by default.
- Return rows as dataclass instances by default.
- Allow callers to disable dataclass conversion and receive dictionaries.
- Normalize CSV headers into valid Python dataclass field names.
- Use a generated random field name when a CSV header is None.
- Use the CSV file name as the generated dataclass class name.
- Store the normalized-to-original header mapping on the generated dataclass.
"""

import csv
import keyword
import re
import uuid
from dataclasses import make_dataclass
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

PathInput = Union[str, Path]
CsvValue = Union[str, List[str], None]
CsvRow = Dict[Optional[str], CsvValue]
CsvTable = List[CsvRow]
DataclassTable = List[Any]
LoadResult = Union[CsvTable, DataclassTable]


def resolve_csv_path(file_path: PathInput) -> Path:
    return Path(file_path).expanduser().resolve()


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


def normalize_field_name(name: Optional[str], used_names: Dict[str, int]) -> str:
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


def build_field_map(headers: List[Optional[str]]) -> Dict[str, Optional[str]]:
    used_names: Dict[str, int] = {}
    return {normalize_field_name(header, used_names): header for header in headers}


def convert_rows_to_dataclasses(
    table: CsvTable, headers: List[Optional[str]], class_name: str = "CsvRow"
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

    if not file_path.exists():
        raise Exception(f"{file_path} not found")

    with file_path.open(encoding=encoding) as fd:
        reader = csv.DictReader(fd)
        table = list(reader)
        headers = reader.fieldnames or []

    if as_dataclass:
        return convert_rows_to_dataclasses(
            table, headers, class_name=normalize_class_name(file_path)
        )

    return table
