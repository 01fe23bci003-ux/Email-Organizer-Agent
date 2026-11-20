# Assignment 6 — Personal Agent Runtime

Run with `python solution.py`. The `run_task` implementation is unchanged;
the admission wrapper reads task counts and prior failures from the existing
audit log. Three requests are admitted per user/session, and two prior
failures of the same skill trigger human escalation on its third attempt.

## Console output

```text
attempt 1: failed
attempt 2: failed
attempt 3: escalated to human (skill failed twice)
attempt 4: rejected (session task limit 3 reached)
```
