# Security

- The workflow uses Git only to read tracked-file history.
- It writes `UPDATE.md` only inside discovered workflow folders.
- It requires no credentials or network access.

## Remaining risks

Running it updates generated documentation files in each detected workflow.
