"""Pandas CSV dumping entry point.

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
- Write CSV records with pandas using UTF-8 with BOM support.
- Always write the CSV header row before data rows.
- Write blank values as empty strings.
"""

import warnings
from pathlib import Path
from typing import Iterable
from typing import Optional
from typing import Sequence
from typing import Union

import pandas as pd

from dump_csv import infer_header
from dump_csv import normalize_table
from dump_csv import TableRow

PathInput = Union[str, Path]


def dump_csv(
        file_path: PathInput,
        table: Iterable[TableRow],
        header: Optional[Sequence[str]] = None,
        encoding: str = 'utf-8-sig') -> None:
    file_path = Path(file_path).expanduser().resolve()
    file_path.parent.mkdir(exist_ok=True, parents=True)

    rows = normalize_table(table)
    if not rows:
        warnings.warn(f'{file_path} table is empty.')

    fieldnames = list(header) if header is not None else infer_header(rows)
    frame = pd.DataFrame(rows, columns=fieldnames)
    frame = frame.fillna('').astype(str)
    frame.to_csv(file_path, index=False, encoding=encoding)


if __name__ == '__main__':
    test_path = Path('/private/tmp/dump_csv_pandas_test.csv')
    dump_csv(
        test_path,
        [{'name': 'Alice', 'age': 42, 'blank': None}],
        header=['name', 'age', 'blank']
    )

    output = test_path.read_text(encoding='utf-8-sig')
    print(output)

    assert output == 'name,age,blank\nAlice,42,\n'
