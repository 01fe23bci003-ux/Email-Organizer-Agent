from __future__ import annotations

from typing import Any


def run_task(user: str, skill: str, outcome: bool) -> dict[str, Any]:
    """Existing task runner; execution result is returned without policy state."""
    return {"user": user, "skill": skill, "success": outcome}


def submit_task(
    audit_log: list[dict[str, Any]],
    user: str,
    session: str,
    skill: str,
    outcome: bool,
) -> str:
    session_tasks = [
        row for row in audit_log
        if row["event"] == "task_request"
        and row["user"] == user
        and row["session"] == session
    ]
    if len(session_tasks) >= 3:
        audit_log.append(
            {"event": "rejected", "user": user, "session": session, "skill": skill}
        )
        return "rejected (session task limit 3 reached)"

    previous_failures = sum(
        row["event"] == "task"
        and row["user"] == user
        and row["skill"] == skill
        and not row["success"]
        for row in audit_log
    )
    audit_log.append(
        {
            "event": "task_request",
            "user": user,
            "session": session,
            "skill": skill,
        }
    )
    if previous_failures >= 2:
        audit_log.append(
            {"event": "escalation", "user": user, "session": session, "skill": skill}
        )
        return "escalated to human (skill failed twice)"

    result = run_task(user, skill, outcome)
    audit_log.append(
        {
            "event": "task",
            "user": user,
            "session": session,
            "skill": skill,
            "success": result["success"],
        }
    )
    return "completed" if result["success"] else "failed"


def main() -> None:
    audit_log: list[dict[str, Any]] = []
    results = [
        submit_task(audit_log, "student-1", "session-1", "summarize", False),
        submit_task(audit_log, "student-1", "session-1", "summarize", False),
        submit_task(audit_log, "student-1", "session-1", "summarize", True),
        submit_task(audit_log, "student-1", "session-1", "summarize", True),
    ]
    assert results == [
        "failed",
        "failed",
        "escalated to human (skill failed twice)",
        "rejected (session task limit 3 reached)",
    ]
    for number, result in enumerate(results, start=1):
        print(f"attempt {number}: {result}")


if __name__ == "__main__":
    main()
