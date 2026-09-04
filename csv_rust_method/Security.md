# Security

- The example writes only to a system temporary-file location.
- CSV content is parsed as data and is never executed.
- This workflow uses the Rust standard library and requires no credentials or
  network access.

## Remaining risks

Large untrusted CSV inputs can consume memory in library callers.
