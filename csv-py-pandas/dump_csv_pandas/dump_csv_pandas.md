# Pandas CSV Dump

## What it does

`dump_csv_pandas.py` provides `dump_csv`, which writes dictionaries or
dataclass instances to a CSV file through pandas. It infers headers when they
are omitted, converts blank values to empty strings, and writes CRLF line
breaks with UTF-8 BOM support by default.

## How to use it

Run this from the workflow folder:

```sh
python -c 'from dump_csv_pandas import dump_csv; dump_csv("example.csv", [{"name": "Ada"}])'
```

The output path may be a string or `pathlib.Path`; the table may contain
dictionaries or dataclass instances.

## Main substeps

1. Resolve the output path and create its parent directories.
2. Normalize dataclass rows and infer headers when they are omitted.
3. Build a pandas data frame and write its header and CRLF-terminated rows.

## Dependencies

This step requires `pandas`, declared in the parent project's `pyproject.toml`.
