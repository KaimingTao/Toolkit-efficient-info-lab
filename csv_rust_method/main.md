# CSV Rust Method

## What it does

`main.rs` creates rows, writes them to a temporary CSV file, reloads them, and
checks that the loaded data matches the original values.

## How to use it

```sh
cargo run
```

Run this command from the workflow folder.

## Main substeps

1. Build example CSV rows.
2. Write rows through the CSV dump function.
3. Load and compare the temporary CSV data.

## Dependencies

This workflow uses the Rust standard library only; see `Cargo.toml`.
