# Required structure for a workflow step

A **step** is an independently runnable script, command, or subproject task.
Each step must provide the following six pieces of information.

1. **Script and header.** The implementation must begin with a concise header
   (module docstring for Python, crate/module documentation for Rust, or a
   leading comment for JavaScript) that states its purpose, inputs, outputs,
   and important side effects.
2. **What it does.** Its README or a dedicated `SPEC.md` must describe the
   problem it solves, expected behavior, and constraints. Small utilities may
   use the header as the short description, provided the repository map links
   to it.
3. **How to use it.** Document a copyable command, required dependencies,
   arguments, input format, output format, and at least one minimal example.
4. **Substeps.** Describe the ordered internal stages, including validation,
   transformation, I/O, error handling, and cleanup where applicable.
5. **Standards.** State the behavioral guarantees and failure cases. Follow
   the CSV rules in `csv-files/README.md` for CSV utilities; use UTF-8,
   `pathlib.Path`-compatible paths, explicit exceptions, and no hard-coded
   machine-specific absolute paths.
6. **Code formatting.** Python must be formatted and linted by Ruff. Rust
   must pass `cargo fmt --check` and `cargo clippy -- -D warnings`. Web assets
   must use consistent two-space indentation and avoid unused code.
