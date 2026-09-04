"""Pandas CSV loading entry point.

Design requirements:
- Accept either a string path or a pathlib.Path object.
- Convert the input path to a resolved pathlib.Path before validation or I/O.
- Expand user home markers such as "~" during path normalization.
- Raise an exception when the resolved file path does not exist.
- Read CSV records with pandas using UTF-8 with BOM support by default.
- Load every CSV value as a string.
- Preserve blank CSV values as empty strings instead of missing values.
- Return rows as dataclass instances by default.
- Allow callers to disable dataclass conversion and receive dictionaries.
- Normalize CSV headers into valid Python dataclass field names.
- Use the CSV file name as the generated dataclass class name.
"""

from pathlib import Path
from typing import Dict
from typing import List
from typing import Union

import pandas as pd

from load_csv import convert_rows_to_dataclasses
from load_csv import normalize_class_name
from load_csv import resolve_csv_path

PathInput = Union[str, Path]
CsvRow = Dict[str, str]
CsvTable = List[CsvRow]
LoadResult = Union[CsvTable, List[object]]


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


def _frame_to_table(frame: pd.DataFrame) -> tuple[CsvTable, List[str]]:
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

    if not file_path.exists():
        raise Exception(f"{file_path} not found")

    table, headers = _frame_to_table(_read_csv_frame(file_path, encoding))

    if as_dataclass:
        return convert_rows_to_dataclasses(
            table, headers, class_name=normalize_class_name(file_path)
        )

    return table


if __name__ == "__main__":
    test_path = Path("/private/tmp/load_csv_pandas_test.csv")
    test_path.write_text("name,age,blank\nAlice,42,\nBob,,x\n", encoding="utf-8")

    rows = load_csv(test_path, as_dataclass=False)
    print(rows)

    assert rows == [
        {"name": "Alice", "age": "42", "blank": ""},
        {"name": "Bob", "age": "", "blank": "x"},
    ]
    assert all(isinstance(value, str) for row in rows for value in row.values())
