from __future__ import annotations

from typing import Any


def main() -> None:
    goal: dict[str, Any] = {"subject": "biology", "exam_date": None}
    iteration_log: list[dict[str, str]] = []

    def log(planned: str, action: str, observed: str, stop_reason: str) -> None:
        entry = {
            "planned": planned,
            "action": action,
            "observed": observed,
            "stop_reason": stop_reason,
        }
        iteration_log.append(entry)
        number = len(iteration_log)
        print(
            f"ITERATION {number}: planned={planned}; action={action}; "
            f"observed={observed}; stop_reason={stop_reason}"
        )

    if goal["exam_date"] is None:
        log("check required goals", "ask for exam_date", "student has no date yet", "continue")
    else:
        log("check required goals", "use exam_date", str(goal["exam_date"]), "continue")

    plan = {
        "id": "plan-1",
        "sessions": [
            {"day": "Monday", "topic": "Cell biology"},
            {"day": "Tuesday", "topic": "Genetics"},
        ],
    }
    original_plan = plan
    log("build initial study plan", "create plan", f"{plan['id']} created", "continue")

    student_update = "I have an exam on Friday"
    if "Friday" in student_update and goal["exam_date"] is None:
        goal["exam_date"] = "Friday"
        log("check for goal changes", "revise existing plan", "exam Friday", "continue")
        plan["sessions"].append({"day": "Thursday", "topic": "Revision"})

    assert plan is original_plan
    assert any(session["day"] == "Thursday" for session in plan["sessions"])
    log("verify revised plan", "stop", "Thursday revision added", "goal satisfied")
    print(f"plan_identity_preserved={plan is original_plan}")

    note = [
        "Chatbot-like: asks a clarifying question about the missing exam date.",
        "Chatbot-like: acknowledges the student's statement about Friday.",
        "Agent-like: tracks exam_date as persistent goal state.",
        "Agent-like: revises the existing plan object instead of regenerating it.",
        "Agent-like: observes the changed goal, adds Thursday revision, and stops when satisfied.",
    ]
    for line in note:
        print(line)


if __name__ == "__main__":
    main()
