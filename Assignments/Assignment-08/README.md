# Assignment 8 — Parallel Swarm: Hackathon Planner

Run with `python solution.py`. Design, engineering, and marketing each have
their own cost and critique role. Objections are tagged with their role. If
the planned total exceeds the shared budget, `budget_over_preference` trims
the preferred campaign scope to meet the cap.

## Console output

```text
initial cost: design=30, engineering=45, marketing=40; total=115; cap=100
conflict: planned cost 115 exceeds shared cap 100
objection [design_agent]: premium venue is not needed for the core experience
objection [engineering_agent]: contingency is too small for the integration risk
objection [marketing_agent]: paid campaign exceeds the remaining budget
resolution [budget_over_preference]: reduce optional marketing spend 40 -> 25; total=100
```
