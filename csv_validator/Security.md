# Security

- Input and output paths are caller-controlled. Confirm output paths before
  using `--write-corrected` because an existing file can be overwritten.
- CSV and YAML configuration contents are parsed as data and are not executed.
- The optional `PyYAML` dependency is used only for configuration parsing; no
  credentials or network access are required.

## Remaining risks

Large or malformed CSV files can consume memory during validation.
