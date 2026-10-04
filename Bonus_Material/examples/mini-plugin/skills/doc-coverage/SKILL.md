---
name: doc-coverage
description: Check an API documentation page for missing sections (description, auth, parameters, response, errors, example). Use when someone asks what is missing or incomplete in a doc.
---

Analyze the file the user names.

## Steps
1. Read the file.
2. For each required section, report PRESENT or MISSING:
   description, authentication, parameters (with types), response example, error codes, at least one working example.
3. For every parameter, flag a missing type or description.

## Constraints
- Report only. Do not edit the file.
- Cite line numbers.

## Output
A table: `Section | Status | Evidence (line)`, then the top 3 fixes, each starting with a verb.
