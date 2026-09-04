# Security

- Output paths are caller-controlled and may overwrite existing files; confirm
  the destination before writing.
- Row values are written as data and are not executed.
- This workflow uses pandas locally and does not require credentials or network
  access.

## Remaining risks

Writing to an unintended caller-supplied path can overwrite a file.
