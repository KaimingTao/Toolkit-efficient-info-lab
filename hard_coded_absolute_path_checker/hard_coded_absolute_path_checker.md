# Hard-Coded Absolute Path Checker

## What it does

This workflow finds hard-coded absolute POSIX and Windows path literals in
Python source files below a folder you provide. It skips `.git`, `.venv`, and
`__pycache__` directories. It prints every violation to standard error and
returns a nonzero exit code when violations exist; otherwise, it reports a
successful check and exits with code zero.

## How to use it

Run the workflow from the repository root, supplying the folder to scan as a
required positional argument:

```sh
uv run python hard_coded_absolute_path_checker/hard_coded_absolute_path_checker.py <folder-path>
```

Its input is the specified folder and every Python file beneath it. Its output
is either a success message or a list of file, line, and column locations
containing absolute path literals. The command fails if the folder argument is
missing or is not a directory.

## Main substeps

1. Validate and resolve the supplied folder path.
2. Find Python source files while excluding the configured generated and
   version-control directories.
3. Parse each file into a Python abstract syntax tree and inspect string
   literals for POSIX or Windows absolute paths.
4. Print all violations and return exit code `1`; print a success message and
   return exit code `0` when none are found.

## Dependencies

This step uses only the Python standard library and inherits the parent
project's Python version requirement from `pyproject.toml`.
