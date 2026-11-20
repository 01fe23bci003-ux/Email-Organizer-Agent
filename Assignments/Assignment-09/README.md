# Assignment 9 — Deep Research Agent: AI Topic Briefing

Run with `python solution.py`. The evidence table includes S1-S4 and their
quality tiers. S4 directly contradicts S1; the synthesis reports a conflict,
not a gap, and gives a cohort/outcome difference as a plausible explanation.
It leans toward peer-reviewed S1 while disclosing that the vendor claim was
down-weighted, not discarded.

## Console output

```text
ID  TIER                     CLAIM
S1  peer-reviewed            AI tutoring improved benchmark scores by 12%.
S2  independent benchmark    AI tutoring improved benchmark scores by 8%.
S3  vendor blog              AI tutoring improved benchmark scores by 20%.
S4  independent benchmark    AI tutoring showed no improvement in a long-form cohort.
Conflict: S4 directly contradicts S1; plausible reason: S1 tests short benchmark tasks, while S4 measures long-form transfer in a different cohort.
Executive summary: The synthesis leans toward S1's 12% benchmark result because it is peer-reviewed. S3's 20% vendor claim is down-weighted, not discarded, because it is lower-tier and lacks independent replication.
```
