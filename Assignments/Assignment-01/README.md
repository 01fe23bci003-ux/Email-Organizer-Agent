# Assignment 1 — Agent vs Chatbot: Study Planner

Run from this directory with `python solution.py`.

The planner asks for `exam_date` only while it is `None`. It creates a plan
once, then revises that same dictionary after the student reports a Friday
exam; Thursday becomes a revision session. Every loop entry records
`planned`, `action`, `observed`, and `stop_reason`.

## Console output

```text
ITERATION 1: planned=check required goals; action=ask for exam_date; observed=student has no date yet; stop_reason=continue
ITERATION 2: planned=build initial study plan; action=create plan; observed=plan-1 created; stop_reason=continue
ITERATION 3: planned=check for goal changes; action=revise existing plan; observed=exam Friday; stop_reason=continue
ITERATION 4: planned=verify revised plan; action=stop; observed=Thursday revision added; stop_reason=goal satisfied
plan_identity_preserved=True
Chatbot-like: asks a clarifying question about the missing exam date.
Chatbot-like: acknowledges the student's statement about Friday.
Agent-like: tracks exam_date as persistent goal state.
Agent-like: revises the existing plan object instead of regenerating it.
Agent-like: observes the changed goal, adds Thursday revision, and stops when satisfied.
```

The five-line classification note is printed by the program; it distinguishes
the clarifying utterance from the stateful planning and revision loop.
