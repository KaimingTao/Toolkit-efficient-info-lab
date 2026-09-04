# CSV Compatibility Problems Across Different Load/Dump Programs

CSV files look simple, but different tools export and import them differently. A file that works in one program may fail, mis-parse, or silently change data in another.

## Validator / Corrector Usage

The repository includes `CSV_validator_corrector.py`, which can validate a CSV file and optionally rewrite it into a configured output format.

The static browser app is in the sibling `../csv_validator_web/` folder:

- `index.html`
- `styles.css`
- `app.js`

Open `../csv_validator_web/index.html` in a browser, load a CSV file, and
choose the target format from the built-in form controls. The app will:

- detect delimiter, newline style, and encoding
- validate the CSV structure and common compatibility risks
- compare the file against the selected target format
- generate a corrected CSV for download in the configured format

The browser app exposes these target format controls directly:

- `delimiter`: `,`, `;`, `\t`, `|`
- `line_terminator`: `\n`, `\r\n`, `\r`
- `encoding`: `utf-8`, `latin-1`, `utf-16`
- `quote_style`: `minimal`, `all`
- `bom`: `true` or `false` for UTF-8 output

The Python CLI still reads its expected output format from `corrector_config.yaml`:

```yaml
expected_output_format:
  delimiter: ","
  line_terminator: "\n"
  encoding: "utf-8"
  quote_style: "minimal"
  bom: false
```

Run validation with the default config:

```bash
python3 CSV_validator_corrector.py test_cases/good_basic.csv
```

Write a corrected file using the configured format:

```bash
python3 CSV_validator_corrector.py test_cases/semicolon_locale.csv --write-corrected corrected.csv
```

Supported `expected_output_format` values:

- `delimiter`: `,`, `;`, `\t`, `|`
- `line_terminator`: `\n`, `\r\n`, `\r`
- `encoding`: `utf-8`, `latin-1`, `utf-16`
- `quote_style`: `minimal`, `all`
- `bom`: `true` or `false` for UTF-8 output

`--config` requires `PyYAML` to be installed.

This document lists the main classes of CSV problems commonly caused by different loaders, dumpers, spreadsheets, databases, ETL tools, scripting libraries, and regional settings.

## 1. Delimiter Differences

Different programs may use different field separators:

- comma: `,`
- semicolon: `;`
- tab: TSV-style
- pipe: `|`
- custom delimiter

Common problems:

- a file exported with `;` is read as a single column by a parser expecting `,`
- tab-delimited files are mislabeled as `.csv`
- data contains the delimiter but is not quoted correctly
- mixed delimiters appear in the same file

## 2. Quote Handling Problems

CSV tools differ on when and how they quote fields.

Common problems:

- some tools quote every field, others only fields that need quoting
- embedded double quotes are not escaped correctly
- a field like `He said "hi"` should usually become `"He said ""hi"""`, but many dumpers get this wrong
- some loaders accept broken quotes, others reject the file
- quote characters may be changed to single quotes by non-standard exporters
- unclosed quoted fields can cause the rest of the row or file to shift

## 3. Newline Differences

Different platforms and tools use different line endings:

- LF: Unix/Linux/macOS modern style
- CRLF: Windows style
- CR: old Mac style

Common problems:

- a parser expects one newline style and mishandles another
- quoted fields may legally contain embedded newlines, but many simple readers split rows incorrectly
- some dumpers produce mixed newline styles in one file
- trailing blank lines may be interpreted as empty records

### What `^M` Means

`^M` usually indicates a carriage return character, `CR`, written as `\r`.

Why it appears as `^M`:

- terminals and text tools often show control characters using caret notation
- carriage return is the control code associated with `Ctrl+M`
- Windows line endings are usually `CRLF` (`\r\n`), while Unix-like systems usually use `LF` (`\n`)
- when a Unix tool shows the `\r` byte explicitly, it often appears as `^M`

Typical implication:

- a file was created or exported with Windows-style line endings and then viewed or processed by a Unix-oriented tool

## 4. Character Encoding Problems

Encoding is one of the most common real-world CSV failure points.

Common problems:

- UTF-8 vs UTF-8 with BOM
- UTF-16 exported by spreadsheet tools
- Latin-1 / ISO-8859-1 vs UTF-8 confusion
- Windows-1252 smart quotes and special symbols breaking UTF-8 readers
- non-ASCII names become garbled
- loaders silently replace invalid bytes with `?` or a replacement character

Typical symptoms:

- mojibake, such as broken accented characters
- header names no longer match expected column names
- parsing succeeds but values are corrupted

## 5. BOM Issues

Some exporters prepend a BOM at the beginning of the file.

Common problems:

- first header becomes `\ufeffid` instead of `id`
- software that does not strip BOM treats the first column name as different
- tools behave differently for UTF-8 BOM vs UTF-16 BOM

## 6. Header Problems

Programs disagree on whether a header row exists and what it should look like.

Common problems:

- header row missing
- header row duplicated
- header row interpreted as data
- first data row interpreted as header
- duplicate column names
- empty column names
- column names with leading or trailing spaces
- case differences like `Name` vs `name`
- hidden BOM in first header cell

## 7. Column Count Inconsistency

Some dumpers emit malformed rows with different numbers of fields.

Common problems:

- short rows with missing trailing values
- long rows caused by broken quoting or extra delimiters
- some parsers pad missing columns with null/empty strings, others fail
- a row may be silently truncated by weak importers

## 8. Null, Empty, and Missing Value Ambiguity

CSV has no universal null representation.

Different tools may use:

- empty string: ``
- quoted empty string: `""`
- literal text: `NULL`
- `N/A`, `NA`, `NaN`, `None`, `nil`, `-`

Common problems:

- empty string and null are merged unintentionally
- literal `NULL` is incorrectly converted to database null
- numeric parsers treat blank as zero
- analytics tools infer missing values differently

## 9. Type Inference Corruption

Many importers guess data types instead of preserving raw text.

Common problems:

- leading zeros dropped: `00123` becomes `123`
- large integers converted to scientific notation
- long IDs rounded because of floating-point limits
- zip codes, account numbers, phone numbers, and SKU values are changed
- boolean-like text such as `TRUE`, `FALSE`, `yes`, `no`, `0`, `1` gets auto-converted
- strings that look like formulas, dates, or numbers are mutated

## 10. Date and Time Parsing Differences

Date/time values are especially inconsistent across tools and locales.

Common problems:

- `01/02/2024` interpreted as January 2 or February 1
- timestamps converted to local timezone without notice
- timezone offsets stripped
- date-only values turned into datetimes
- datetimes reformatted into locale-specific strings
- Excel-style serial dates appear unexpectedly
- invalid dates are normalized instead of rejected

## 11. Locale and Regional Setting Issues

Regional settings strongly affect CSV behavior.

Common problems:

- decimal comma vs decimal point: `3,14` vs `3.14`
- semicolon used as delimiter because comma is reserved for decimals
- thousands separators differ: `1,000`, `1.000`, `1 000`
- date formats differ by region
- month names and localized boolean values vary

## 12. Whitespace Problems

Whitespace handling differs between parsers.

Common problems:

- leading/trailing spaces around headers or values are preserved by one tool and trimmed by another
- spaces after delimiters may or may not be ignored
- tabs mixed into cells unexpectedly
- non-breaking spaces appear visually normal but break matching

## 13. Escaping Rules Are Not Universal

Not all tools follow RFC-like CSV escaping behavior.

Common problems:

- backslash escaping used instead of doubled quotes
- custom escape characters used without metadata
- delimiters inside unquoted fields
- quote escaping rules differ between libraries

## 14. Embedded Special Characters

Cell values may contain characters that some tools mishandle.

Common problems:

- embedded commas
- embedded quotes
- embedded newlines
- tabs
- carriage returns
- Unicode separators or invisible characters

These are valid in many CSV dialects when quoted correctly, but not all tools support them reliably.

## 15. Spreadsheet-Specific Damage

Spreadsheet programs often modify data on open or save.

Common problems:

- formulas interpreted instead of preserved as text
- CSV injection risk for values starting with `=`, `+`, `-`, or `@`
- long numbers displayed or saved in scientific notation
- leading zeros removed
- whitespace normalized
- encoding changed on save
- line breaks inside cells lost or rewritten
- separators changed based on OS locale

## 16. Database Export/Import Differences

Database tools often use their own CSV dialect or null conventions.

Common problems:

- explicit null tokens differ by database
- export includes quotes only sometimes
- import requires exact column order
- server-side export uses different encoding than client-side import
- bulk loaders reject rows that scripting libraries would accept
- control characters may be disallowed

## 17. Library-Specific Dialect Differences

Programming libraries often expose different defaults.

Examples of varying defaults:

- delimiter
- quote character
- escape character
- double-quote behavior
- line terminator
- strict vs permissive parsing
- whether malformed rows are skipped, repaired, or rejected

Common problems:

- Python, pandas, Excel, database loaders, and shell tools all parse the same file differently
- one library accepts malformed data that another rejects later in production

## 18. Duplicate, Missing, or Reordered Columns

Some loaders map by position, others by name.

Common problems:

- reordered columns break downstream consumers
- duplicate headers overwrite earlier columns in map-based loaders
- optional columns disappear during export
- extra columns are silently ignored

## 19. Comments and Non-Data Lines

Some tools support comment lines or metadata rows, others do not.

Common problems:

- lines beginning with `#` are treated as comments by one parser and data by another
- export tools prepend metadata banners
- blank lines may be ignored or parsed as empty rows

## 20. Truncation and Size Limits

Programs may impose row, column, or cell size limits.

Common problems:

- spreadsheet row limits truncate large datasets
- very wide fields are clipped
- import UI previews only partial data
- memory-limited tools fail on large files
- buffer limits cut off long lines

## 21. Control Characters and Invalid Bytes

Some CSV files contain hidden characters that break import.

Common problems:

- NUL bytes inside fields
- unprintable control characters
- mixed binary/text content
- invalid UTF byte sequences

Some parsers reject these immediately. Others silently strip them.

## 22. Inconsistent Row Termination at End of File

Common problems:

- last row missing final newline
- some parsers accept it, others report a malformed file
- partially written export files may end mid-row

## 23. File Naming and Extension Confusion

Common problems:

- `.csv` file is actually TSV or pipe-delimited
- compressed or encrypted file renamed as CSV
- encoding or dialect not discoverable from file extension alone

## 24. Silent Data Loss During Round-Trip

Opening and resaving a CSV through a different tool can change data even when no error is shown.

Common problems:

- formatting normalized
- quotes removed or added
- null markers changed
- date/time text rewritten
- precision lost
- column order changed
- empty trailing columns dropped

## 25. Error Handling Differences

Different programs fail differently:

- strict reject
- permissive accept
- partial import with warnings
- silent repair
- silent corruption

This is one of the hardest CSV problems because success does not guarantee correctness.

## Practical Validation Checklist

If you want a CSV validator to be useful across many load/dump programs, it should check at least:

- detected delimiter
- newline style
- encoding and BOM
- consistent column count
- header validity
- quote and escape correctness
- embedded newline handling
- null/empty conventions
- duplicate columns
- suspicious whitespace
- type-sensitive fields such as IDs, dates, and long integers
- control characters and invalid bytes
- round-trip risk warnings for spreadsheet software

## Bottom Line

CSV is not one strict format in practice. It is a family of loosely related dialects with different defaults, assumptions, and silent conversion behaviors.

A robust CSV validation workflow should assume:

- the producer and consumer may use different dialects
- parsing success is not enough
- preserving exact data values matters as much as structural validity
