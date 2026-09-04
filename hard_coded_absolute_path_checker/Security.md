# Security

- The folder path is caller-controlled. It is resolved and must be a directory
  before source files are scanned.
- Source files are parsed as Python syntax; they are never executed.
- This workflow uses only the Python standard library and does not require
  credentials or network access.

## Remaining risks

Scanning a very large folder can consume memory and processing time.
