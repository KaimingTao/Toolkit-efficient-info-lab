# Pandas CSV Load

## What it does

`load_csv_pandas.py` provides `load_csv`, which reads CSV values as strings
through pandas. Blank values remain empty strings, and callers may receive
dictionaries or generated dataclass instances.

## How to use it

Run this from the workflow folder:

```sh
python -c 'from load_csv_pandas import load_csv; print(load_csv("<input.csv>", as_dataclass=False))'
```

The input must identify an existing CSV file. Set `as_dataclass=False` to
receive dictionaries.

## Main substeps

1. Resolve and validate the input path.
2. Read the source into a pandas data frame without converting blanks to nulls.
3. Return dictionary rows or convert them to generated dataclass instances.

## Dependencies

This step requires `pandas`, declared in the parent project's `pyproject.toml`.
