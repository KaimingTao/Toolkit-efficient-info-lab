# Quality Control

## Python code quality

Install Ruff as a development dependency, format the Python files, then apply
Ruff's automatic lint fixes:

```sh
uv add --dev ruff
uv run ruff format .
uv run ruff check . --fix
```

Check Python source code for hard-coded absolute paths from the repository
root:

```sh
uv run python hard_coded_absolute_path_checker/hard_coded_absolute_path_checker.py <folder-path>
```
