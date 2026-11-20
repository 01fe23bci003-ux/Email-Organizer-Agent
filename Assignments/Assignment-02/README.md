# Assignment 2 — Tool-Using Agent: Campus Data Assistant

Run with `python solution.py`. The mock CSV includes both `technical` and
`social` categories. The trace shows `read_csv`, one filter per category, and
two separate calculator calls. The agent checks each filtered list before
calculating its average.

## Tool schemas and console output

```text
read_csv(path: str) -> list[dict[str, str]]
filter_by_category(rows: list[dict[str, str]], category: str) -> list[dict[str, str]]
calculator(values: list[float]) -> float
TRACE read_csv -> 4 rows
TRACE filter_by_category(technical) -> 2 rows
TRACE calculator(technical) -> 100.0
TRACE filter_by_category(social) -> 2 rows
TRACE calculator(social) -> 125.0
Final answer: social has the higher average sign-ups (125.0 vs 100.0).
TRACE filter_by_category(arts) -> 0 rows
Empty category validation: No sign-up rows found for category 'arts'.
```
