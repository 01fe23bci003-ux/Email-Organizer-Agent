# Assignment 7 — Agentic Node Graph: Campus App Builder

Run with `python solution.py`. The graph places `security_scan` between
`builder` and `tester`. Builder gets exactly one retry; a second failure
escalates. Scan failure halts before testing.

## Node graph

```text
[planner] -> [builder] --fail (1 retry)--> [builder]
                  | success
                  v
          [security_scan] -> [tester] -> [release]
                  |
                  +-- fail --> [human escalation]
builder fails twice --------------------> [human escalation]
```

## Execution traces

```text
CASE (a)
  planner: specification ready
  builder attempt 1: failure
  builder attempt 2: success
  security_scan: pass
  tester: pass
  release: ready for human approval
CASE (b)
  planner: specification ready
  builder attempt 1: failure
  builder attempt 2: failure
  human escalation: builder retry limit reached
CASE (c)
  planner: specification ready
  builder attempt 1: success
  security_scan: fail
  human escalation: security scan failed; tester not run
```
