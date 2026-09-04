# Required structure for a workflow step

A **step** is an independently runnable script, command, or subproject task.
Each step must contain these four parts.

1. **Main workflow entry.** Provide one clearly identified executable entry
   point: for example, a script, CLI command, application page, or `main`
   function. The workflow document must name this entry and the command used
   to run it.
2. **Workflow document.** Provide a Markdown document beside the entry point
   with the same base name as the entry file. For example, `load_csv.py` must
   use `load_csv.md`; `main.rs` must use `main.md`. It must state:
   - what the workflow does and its expected result;
   - how to use it, including dependencies, inputs, outputs, and a copyable
     example command; and
   - its main substeps in execution order, including validation,
     transformation, I/O, and error handling where applicable.
3. **Source-file headers.** Every programming-language source file must begin
   with a short header: a module docstring in Python, documentation comment in
   Rust, or leading comment in JavaScript and other languages. The header must
   be a concise copy of the relevant workflow document: identify the workflow,
   say what this file does within it, show or point to the usage, and summarize
   the file's main substeps. Update the header whenever the workflow document
   changes.
4. **Dedicated workflow folder and tests.** Place every workflow step in its
   own folder. That folder must contain the entry file, its same-named workflow
   document, and the implementation files. Test code and test cases (fixtures
   or sample inputs and their expected outputs) are optional; when present,
   keep them within the workflow folder rather than in a shared unrelated
   location.

## Formatting and linting

Every programming-language source file must be formatted and linted with the
project's language-appropriate tools before it is committed. For example, use
Ruff for Python, `cargo fmt` and Clippy for Rust, and the configured formatter
and linter for JavaScript or other languages.

## Dependencies

Dependencies must be clearly documented in the workflow step's same-named
workflow document. When a step does not declare its own dependencies, it uses
the dependencies declared by its parent step.

## Safety

Code must be reviewed and monitored for security risks. Before committing,
check that inputs are validated, sensitive data is not exposed, dependencies
are appropriate, and the workflow does not introduce unsafe file, network, or
command execution behavior. Each workflow folder must include a `Security.md`
file that records its security concerns, risk mitigations, and any remaining
risks. If no concerns are identified, the file must explicitly say so.
