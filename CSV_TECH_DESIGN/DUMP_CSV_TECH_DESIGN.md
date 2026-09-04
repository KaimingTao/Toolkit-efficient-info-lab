# CSV Dump Technical Design

## Path input

Accept either a string path or a `pathlib.Path` object.

## Path normalization

Convert the input path to a resolved `pathlib.Path` and expand user home
markers such as `~` before validation or I/O.

## Output directories

Create missing parent directories before writing.

## Accepted table rows

Accept a table as a list of dictionaries or dataclass instances.

## Cell validation

Do not validate cell values by default.

## Empty tables

Warn when asked to dump an empty table.

## Optional headers

Allow the header argument to be omitted.

## Header inference

Infer CSV headers from row keys or dataclass fields when no header is provided.

## Header order

Preserve inferred header order by first occurrence while scanning rows.

## CSV encoding and writer

Write CSV records with `csv.DictWriter` using UTF-8 with BOM support.

## Line terminator

Always write records with the full CRLF (`\r\n`) line-break sequence.

## Header output

Always write the CSV header row before data rows.
