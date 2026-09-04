# Security

- Input paths are caller-controlled and are resolved and checked as regular
  files before reading.
- CSV contents are treated as data and are not executed.
- This workflow uses pandas locally and does not require credentials or network
  access.

## Remaining risks

Large or untrusted CSV files can consume memory when loaded into a data frame.
