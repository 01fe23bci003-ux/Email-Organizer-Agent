# Assignment 4 — Memory and Retrieval: Project Memory

Run with `python solution.py`. Records are stored by topic, and retrieval
consults only the requested topic. `retention_days=30`; records older than the
cutoff produce a warning before their content is returned.

## Console output

```text
retrieve(database): Fresh database note
retrieve(hosting): WARNING: record is 60 days old (retention is 30 days); verify before use.
retrieve(hosting): Old hosting note
topic isolation: database result contains no hosting record
```
