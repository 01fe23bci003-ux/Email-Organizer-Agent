from typing import Any


REQUIRED_FIELDS = (
    "mailbox_scope",
    "priority_categories",
    "date_range",
    "standard_response_library_available",
)

SIMULATED_ANSWERS: dict[str, Any] = {
    "mailbox_scope": "faculty_inbox",
    "priority_categories": ["urgent", "high", "medium", "low"],
    "date_range": "all_unprocessed",
    "standard_response_library_available": True,
}


class EmailOrganizerPlannerAgent:
    """A small, inspectable clarify-plan-revise loop for the Lab 1 demo."""

    def __init__(self) -> None:
        self.goal: dict[str, Any] = {field: None for field in REQUIRED_FIELDS}
        self.plan: dict[str, Any] | None = None
        self.log: list[dict[str, str]] = []
        self.clarifying_questions_asked = 0

    def next_step(self) -> tuple[str, str | None]:
        for field in REQUIRED_FIELDS:
            if self.goal[field] is None:
                return "ask", field
        return "generate_plan", None

    def run(self, answers: dict[str, Any] | None = None) -> dict[str, Any]:
        simulated_answers = answers or SIMULATED_ANSWERS
        while True:
            action, field = self.next_step()
            if action == "generate_plan":
                self.plan = {
                    "goal": dict(self.goal),
                    "categories": [
                        "student",
                        "faculty",
                        "administration",
                        "collaborator",
                        "vendor",
                        "other",
                    ],
                    "steps": [
                        "Read inbox threads in the selected scope and date range",
                        "Verify sender category using contacts and thread history",
                        "Prioritize messages using the selected priority categories",
                        "Prepare grounded reply drafts and action-item suggestions",
                        "Present results for mailbox-owner review; never send automatically",
                    ],
                    "approval_required_before_send": True,
                }
                self.log.append(
                    {
                        "planned": "Generate triage plan from clarified requirements",
                        "action": "generate_plan",
                        "observed": "Plan created and ready for owner review",
                        "stopped": "Awaiting owner review",
                    }
                )
                return self.plan

            assert field is not None
            self.clarifying_questions_asked += 1
            observed = simulated_answers.get(field)
            self.log.append(
                {
                    "planned": f"Clarify {field}",
                    "action": "ask",
                    "observed": f"{field}={observed!r}",
                    "stopped": "" if observed is not None else f"Missing answer: {field}",
                }
            )
            if observed is None:
                raise ValueError(f"No answer supplied for required planning field: {field}")
            self.goal[field] = observed

    def revise(self, feedback: dict[str, Any]) -> dict[str, Any]:
        if self.plan is None:
            raise RuntimeError("Run the planner before revising its plan")
        category_merges = feedback.get("merge_categories", {})
        categories = self.plan["categories"]
        for source, target in category_merges.items():
            if source in categories and target in categories:
                categories.remove(source)
                self.plan["categories"] = list(dict.fromkeys(categories))
                self.log.append(
                    {
                        "planned": f"Apply owner feedback: merge {source} into {target}",
                        "action": "revise",
                        "observed": f"{source} removed; {target} retained",
                        "stopped": "",
                    }
                )
        return self.plan