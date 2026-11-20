from __future__ import annotations

from typing import Any


class Governance:
    def __init__(self, budget_threshold: float) -> None:
        self.budget_threshold = budget_threshold
        self.proposals_since_evaluation = 0
        self.audit_log: list[dict[str, Any]] = []

    def propose(
        self,
        proposal_id: str,
        cost_estimate: float | None = None,
        finance_approved: bool = False,
    ) -> str:
        if self.proposals_since_evaluation >= 5:
            message = "blocked (re-evaluation required after 5 proposals)"
            self.audit_log.append({"id": proposal_id, "decision": message})
            return message

        self.proposals_since_evaluation += 1
        if cost_estimate is None:
            message = "rejected (cost estimate required)"
        elif cost_estimate > self.budget_threshold and not finance_approved:
            message = "rejected (over budget; finance approval required)"
        elif cost_estimate > self.budget_threshold:
            message = "approved (finance approval recorded)"
        else:
            message = "approved"
        self.audit_log.append({"id": proposal_id, "decision": message})
        return message

    def evaluate(self) -> None:
        self.proposals_since_evaluation = 0
        self.audit_log.append({"event": "evaluation", "decision": "re-evaluated"})


def main() -> None:
    governance = Governance(budget_threshold=100.0)
    results = [
        governance.propose("P1"),
        governance.propose("P2", cost_estimate=120.0),
        governance.propose("P3", cost_estimate=120.0, finance_approved=True),
        governance.propose("P4", cost_estimate=80.0),
        governance.propose("P5", cost_estimate=60.0),
    ]
    for number, result in enumerate(results, start=1):
        print(f"proposal P{number}: {result}")
    assert results[0].startswith("rejected")
    assert results[1].startswith("rejected")
    sixth = governance.propose("P6", cost_estimate=50.0)
    print(f"proposal P6: {sixth}")
    assert sixth.startswith("blocked")
    governance.evaluate()
    print("evaluate(): governance re-evaluated; proposal counter reset")
    seventh = governance.propose("P7", cost_estimate=50.0)
    print(f"proposal P7: {seventh}")
    assert seventh == "approved"
    for row in governance.audit_log:
        print(f"AUDIT {row}")
    decisions = [row for row in governance.audit_log if "id" in row]
    print(
        f"audit log: {len(governance.audit_log)} entries "
        f"({len(decisions)} proposal decisions, "
        f"{len(governance.audit_log) - len(decisions)} evaluation)"
    )


if __name__ == "__main__":
    main()
