# Generate Update Files

## What it does

Generates an empty `updated_at_YYYY-MM-DD.md` file in each workflow folder that
has a documented source entry. The date is the most recent Git commit date
affecting tracked files there.

## How to use it

```sh
uv run python generate_update_files/generate_update_files.py
```

## Main substeps

1. Find source entry files with same-named Markdown workflow documents.
2. Query Git for the latest tracked-file commit date in each workflow folder.
3. Remove any previous date marker and write the new empty date-named marker.

## Dependencies

Uses the Python standard library and the Git command-line tool.
