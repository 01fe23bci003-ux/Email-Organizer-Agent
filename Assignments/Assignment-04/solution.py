from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class MemoryRecord:
    topic: str
    content: str
    created_at: datetime


class ProjectMemory:
    def __init__(self, retention_days: int, now: datetime) -> None:
        self.retention_days = retention_days
        self.now = now
        self.records: list[MemoryRecord] = []

    def store(self, record: MemoryRecord) -> None:
        self.records.append(record)

    def retrieve(self, topic: str) -> list[str]:
        matches = [record for record in self.records if record.topic == topic]
        results: list[str] = []
        cutoff = self.now - timedelta(days=self.retention_days)
        for record in matches:
            if record.created_at < cutoff:
                age = (self.now - record.created_at).days
                results.append(
                    f"WARNING: record is {age} days old "
                    f"(retention is {self.retention_days} days); verify before use."
                )
            results.append(record.content)
        return results


def main() -> None:
    now = datetime(2026, 11, 20, tzinfo=timezone.utc)
    memory = ProjectMemory(retention_days=30, now=now)
    memory.store(MemoryRecord("database", "Fresh database note", now - timedelta(days=2)))
    memory.store(MemoryRecord("hosting", "Old hosting note", now - timedelta(days=60)))

    database = memory.retrieve("database")
    hosting = memory.retrieve("hosting")
    print(f"retrieve(database): {database[0]}")
    print(f"retrieve(hosting): {hosting[0]}")
    print(f"retrieve(hosting): {hosting[1]}")
    assert all("hosting" not in item.lower() for item in database)
    assert all("database" not in item.lower() for item in hosting)
    assert hosting[0].startswith("WARNING:")
    print("topic isolation: database result contains no hosting record")


if __name__ == "__main__":
    main()
