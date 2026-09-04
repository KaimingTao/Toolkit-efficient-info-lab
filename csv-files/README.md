# CSV Design Requirements

## Loading CSV

### Locate the file

- Accept either a string path or a `pathlib.Path` object.
- Convert the input path to a resolved `pathlib.Path` before validation or I/O.
- Expand user home markers such as `~` during path normalization.
- Raise an exception when the resolved file path does not exist.

### file parsing

- Read CSV records with `csv.DictReader` using UTF-8 with BOM support by default.
- Return rows as dataclass instances by default.
- Allow callers to disable dataclass conversion and receive dictionaries.
- Normalize CSV headers into valid Python dataclass field names.
- Use a generated random field name when a CSV header is `None`.
- Use the CSV file name as the generated dataclass class name.
- Store the normalized-to-original header mapping on the generated dataclass.

## Dumping CSV

- Accept either a string path or a `pathlib.Path` object.
- Convert the input path to a resolved `pathlib.Path` before validation or I/O.
- Expand user home markers such as `~` during path normalization.
- Create missing parent directories before writing.
- Accept a table as a list of dictionaries or dataclass instances.
- Do not validate cell values by default.
- Warn when asked to dump an empty table.
- Allow the header argument to be omitted.
- Infer CSV headers from row keys or dataclass fields when no header is provided.
- Preserve inferred header order by first occurrence while scanning rows.
- Write CSV records with `csv.DictWriter` using UTF-8 with BOM support.
- Always write the CSV header row before data rows.

## Python code quality

Install Ruff as a development dependency, format the Python files, then apply
Ruff's automatic lint fixes:

```sh
uv add --dev ruff
uv run ruff format .
uv run ruff check . --fix
```

Check Python source code for hard-coded absolute paths:

```sh
uv run python hard_coded_absolute_path_checker/hard_coded_absolute_path_checker.py <folder-path>
```
