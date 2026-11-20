from __future__ import annotations

import csv
import io
from typing import Any


CSV_DATA = """event,signups,category
robotics workshop,120,technical
coding clinic,80,technical
cultural night,150,social
film club meetup,100,social
"""

TOOL_SCHEMAS = {
    "read_csv": "read_csv(path: str) -> list[dict[str, str]]",
    "filter_by_category": (
        "filter_by_category(rows: list[dict[str, str]], category: str) "
        "-> list[dict[str, str]]"
    ),
    "calculator": "calculator(values: list[float]) -> float",
}


def read_csv(path: str) -> list[dict[str, str]]:
    del path
    return list(csv.DictReader(io.StringIO(CSV_DATA)))


def filter_by_category(
    rows: list[dict[str, str]], category: str
) -> list[dict[str, str]]:
    return [row for row in rows if row["category"] == category]


def calculator(values: list[float]) -> float:
    if not values:
        raise ValueError("calculator requires at least one value")
    return sum(values) / len(values)


def average_for(rows: list[dict[str, str]], category: str) -> float | str:
    filtered = filter_by_category(rows, category)
    print(f"TRACE filter_by_category({category}) -> {len(filtered)} rows")
    if not filtered:
        return f"No sign-up rows found for category '{category}'."
    average = calculator([float(row["signups"]) for row in filtered])
    print(f"TRACE calculator({category}) -> {average:.1f}")
    return average


def main() -> None:
    rows = read_csv("campus_events.csv")
    print(f"TRACE read_csv -> {len(rows)} rows")
    averages: dict[str, float] = {}
    for category in ("technical", "social"):
        result = average_for(rows, category)
        if not isinstance(result, float):
            raise RuntimeError(f"Unexpected empty category: {result}")
        averages[category] = result
    higher = max(averages, key=averages.get)
    print(
        f"Final answer: {higher} has the higher average sign-ups "
        f"({averages[higher]:.1f} vs {averages['technical' if higher == 'social' else 'social']:.1f})."
    )
    assert averages == {"technical": 100.0, "social": 125.0}
    empty_category = average_for([], "arts")
    assert isinstance(empty_category, str)
    print(f"Empty category validation: {empty_category}")


if __name__ == "__main__":
    main()
