# Assignment 12 — Safety, Evaluation and Governance

Run with `python solution.py`. Proposals without cost estimates are rejected;
over-budget proposals require `finance_approved=True`. Every submitted
proposal, including a rejected one, is audited. After five submissions the
sixth is blocked until `evaluate()` records a fresh evaluation.

## Console output

```text
proposal P1: rejected (cost estimate required)
proposal P2: rejected (over budget; finance approval required)
proposal P3: approved (finance approval recorded)
proposal P4: approved
proposal P5: approved
proposal P6: blocked (re-evaluation required after 5 proposals)
evaluate(): governance re-evaluated; proposal counter reset
proposal P7: approved
AUDIT {'id': 'P1', 'decision': 'rejected (cost estimate required)'}
AUDIT {'id': 'P2', 'decision': 'rejected (over budget; finance approval required)'}
AUDIT {'id': 'P3', 'decision': 'approved (finance approval recorded)'}
AUDIT {'id': 'P4', 'decision': 'approved'}
AUDIT {'id': 'P5', 'decision': 'approved'}
AUDIT {'id': 'P6', 'decision': 'blocked (re-evaluation required after 5 proposals)'}
AUDIT {'event': 'evaluation', 'decision': 're-evaluated'}
AUDIT {'id': 'P7', 'decision': 'approved'}
audit log: 8 entries (7 proposal decisions, 1 evaluation)
```
