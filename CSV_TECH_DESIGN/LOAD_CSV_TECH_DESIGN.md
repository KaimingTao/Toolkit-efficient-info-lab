# CSV Load Technical Design

## Path input

Accept either a string path or a `pathlib.Path` object.

## Path normalization

Convert the input path to a resolved `pathlib.Path` and expand user home
markers such as `~` before validation or I/O.

## Missing files

Raise an exception when the resolved file path does not exist.

## CSV file detection

Before parsing, require the input to be a regular file with a
case-insensitive `.csv` extension. Raise an exception when it is not.

## CSV parsing

Read CSV records with `csv.DictReader` using UTF-8 with BOM support by default.

## Line-break handling

Open CSV files with `newline=""` so the CSV parser receives complete line-break
sequences without Python newline translation.

## Line-break detection

Inspect the source bytes and report CRLF (`\r\n`), LF (`\n`), CR (`\r`), mixed,
or no line breaks through `detect_csv_file_format`.

## BOM detection

Inspect the source bytes and report whether a UTF-8, UTF-16 little-endian, or
UTF-16 big-endian byte-order mark is present through `detect_csv_file_format`.

## Default return type

Return rows as dataclass instances by default.

## Dictionary return type

Allow callers to disable dataclass conversion and receive dictionaries.

## Header normalization

Normalize CSV headers into valid Python dataclass field names.

## Missing headers

Use a generated random field name when a CSV header is `None`.

## Generated class name

Use the CSV file name as the generated dataclass class name.

## Header mapping

Store the normalized-to-original header mapping on the generated dataclass.
