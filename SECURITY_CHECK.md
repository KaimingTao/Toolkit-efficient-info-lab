# Security Checks

Use this checklist when reviewing code in this repository.

- Do not commit access tokens, API keys, passwords, private keys, or other
  credentials. Read them from an approved secret store or environment variable
  at runtime.
- Do not hard-code machine-specific absolute paths. Use paths relative to the
  workflow or user-supplied paths, then validate and resolve them safely.
