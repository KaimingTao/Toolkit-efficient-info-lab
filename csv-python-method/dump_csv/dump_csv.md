# Dump CSV

## What it does

`dump_csv.py` provides the `dump_csv` function. It writes an iterable of
dictionaries or dataclass instances to a CSV file using UTF-8 with BOM support
by default. If no header is supplied, it infers one in first-occurrence order.
It creates missing parent directories, writes CRLF (`\r\n`) record terminators,
and warns when the table is empty.

## How to use it

Run this from the workflow folder:

```sh
python -c 'from dump_csv import dump_csv; dump_csv("example.csv", [{"name": "Ada"}])'
```

The output path may be a string or `pathlib.Path`. The input table is an
iterable of dictionaries or dataclass instances. Pass `header` to set column
order, or omit it to infer headers.

## Main substeps

1. Expand and resolve the requested output path, then create missing parent
   directories.
2. Convert dataclass rows to dictionaries and infer the header when needed.
3. Write the header followed by CRLF-terminated rows through `csv.DictWriter`.

## Dependencies

This step uses only the Python standard library. It inherits the parent
project's Python version requirement from `pyproject.toml`.
