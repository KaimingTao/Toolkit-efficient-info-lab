# Security

## Concerns and mitigations

- The input path is caller-controlled. It is expanded, resolved, and checked
  to ensure it is an existing regular file with a `.csv` extension before
  reading.
- File bytes are inspected only to detect BOM presence and line-break style;
  CSV contents are not executed as code.
- CSV contents are treated as data and are not executed as code.
- This workflow uses only Python standard-library modules and does not require
  credentials or network access.

## Remaining risks

Large or untrusted CSV files can consume memory because all rows are loaded at
once. Use trusted, reasonably sized inputs or add size limits before using it
with untrusted data.
