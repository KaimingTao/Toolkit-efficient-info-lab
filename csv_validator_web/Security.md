# Security

- The application processes user-selected files locally in the browser and does
  not upload them.
- CSV contents are treated as data; avoid inserting untrusted values as HTML.
- Downloads are created from locally generated data. The workflow requires no
  credentials, network access, or third-party runtime dependencies.

## Remaining risks

Very large selected files can consume browser memory.
