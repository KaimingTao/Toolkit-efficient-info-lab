# Load CSV

## What it does

`load_csv.py` provides the `load_csv` function. It reads a CSV file with
UTF-8 BOM support by default and returns generated dataclass instances unless
`as_dataclass=False` is supplied. It normalizes headers into valid dataclass
field names, preserves CSV line endings during parsing, and stores the
normalized-to-original mapping on the generated class. Before parsing, it also
detects whether the source bytes have a UTF BOM and whether line breaks are
CRLF, LF, CR, mixed, or absent.

## How to use it

Run this from the workflow folder:

```sh
python -c 'from load_csv import load_csv; print(load_csv("<input.csv>", as_dataclass=False))'
```

The input path may be a string or `pathlib.Path` and must identify an existing
regular file with a case-insensitive `.csv` extension. Set `as_dataclass=False`
to receive dictionaries instead of dataclass instances.

## Main substeps

1. Expand and resolve the input path.
2. Detect a CSV file by verifying that it is a regular file with a
   case-insensitive `.csv` extension.
3. Inspect the source bytes to detect BOM presence and line-break style.
4. Open the file with `newline=""` and read rows and headers using
   `csv.DictReader`.
5. Return dictionaries or normalize headers and convert rows to a generated
   dataclass.

## Dependencies

This step uses only the Python standard library. It inherits the parent
project's Python version requirement from `pyproject.toml`.
