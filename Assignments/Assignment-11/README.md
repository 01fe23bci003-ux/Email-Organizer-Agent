# Assignment 11 — Agentic SDLC Factory: Mini Software Team

Run with `python solution.py`. The factory tracks story-to-artifact lineage for
US-1 and US-2. The coding agent contains a deliberate urgent-filter bug; the
testing agent is independent and uses explicit acceptance expectations. The
captured test report includes a failing assertion, and the review agent rejects
the release.

## Console output

```text
test_filter_urgent (independent): FAIL - expected urgent message id 2, got []
test_export_pdf (independent): PASS - PDF header and story content present
lineage US-1: filter.py <- coding_agent
lineage US-2: export_pdf.py <- coding_agent
test summary: 1 passed, 1 failed
review agent: REJECT release (independent acceptance test failed)
```
