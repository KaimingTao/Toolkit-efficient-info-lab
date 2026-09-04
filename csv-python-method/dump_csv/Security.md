# Security

## Concerns and mitigations

- The output path is caller-controlled. It is expanded and resolved before
  writing; callers must provide an intended writable path because existing
  files can be overwritten.
- Row data is written as CSV data only and is not executed as code.
- This workflow uses only Python standard-library modules and does not require
  credentials or network access.

## Remaining risks

Writing to an unintended caller-supplied path can overwrite a file. Confirm the
destination before calling `dump_csv`.
