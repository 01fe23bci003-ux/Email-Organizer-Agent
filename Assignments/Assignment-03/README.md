# Assignment 3 — Skill Creation: Research Summary

Run with `python solution.py`. Four deterministic source records include two
baseline articles, a hedged article with competing claims, and a low-evidence
article. The same `research_summary_skill` and `reusability_check` process all
four inputs. Missing source details are emitted as `not stated in source`.

## Console output

```text
article-1: selected="Active recall improves retention"; why=the source reports a controlled comparison; evidence=controlled comparison; limitation=not stated in source
article-2: selected="Short breaks support focus"; why=the source reports participant observations; evidence=participant observations; limitation=not stated in source
article-3: selected="Structured practice improves accuracy"; why=it is supported by measured comparison, while the competing claim has no evidence in the source; evidence=measured comparison; limitation=small sample
article-4: selected="The app improves focus"; why=it is the article's only explicit claim, but no supporting evidence is supplied; evidence=not stated in source; limitation=not stated in source
reusability_check: 4/4 articles processed
No fabrication: confirmed
```
