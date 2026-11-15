import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.connectors.email_connector import EmailConnector, connector


class AdvancedLabsService:
    """Deterministic, auditable demonstrations for Labs 9-14."""

    def __init__(self, data_connector: EmailConnector = connector) -> None:
        self.connector = data_connector
        self.records: list[dict[str, Any]] = []

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:10]}"

    @staticmethod
    def _tokens(value: str) -> set[str]:
        ignored = {"about", "after", "before", "could", "email", "emails", "from", "have", "inbox", "into", "please", "that", "their", "there", "this", "with", "would"}
        return {token for token in re.findall(r"[a-z0-9]+", value.casefold()) if len(token) > 2 and token not in ignored}

    def _record(self, lab: int, workflow: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = {
            "id": self._id(f"lab{lab}"),
            "lab": lab,
            "workflow": workflow,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        self.records.insert(0, record)
        self.connector.save_audit_log({
            "agent": f"Lab {lab} {workflow}",
            "action": "workflow_run",
            "status": "success",
            "details": {"record_id": record["id"], "simulation": True},
        })
        return record

    def _evidence(self, query: str, email_ids: list[str] | None = None, limit: int = 6) -> list[dict[str, Any]]:
        terms = self._tokens(query)
        selected = set(email_ids or [])
        scored: list[tuple[int, dict[str, Any]]] = []
        for email in self.connector.read_inbox():
            if selected and email["id"] not in selected:
                continue
            haystack = f"{email['subject']} {email['body']} {email['sender_category']} {' '.join(email.get('tags', []))}"
            overlap = len(terms & self._tokens(haystack))
            scored.append((overlap, email))
        scored.sort(key=lambda item: (item[0], item[1]["timestamp"]), reverse=True)
        matches = [email for score, email in scored if score > 0][:limit] if terms else [email for _, email in scored[:limit]]
        return [
            {
                "citation": f"[{email['id']}]",
                "email_id": email["id"],
                "sender": email["sender"],
                "subject": email["subject"],
                "category": email["sender_category"],
                "timestamp": email["timestamp"],
                "excerpt": email["body"][:280],
            }
            for email in matches
        ]

    def research(self, question: str, email_ids: list[str] | None = None) -> dict[str, Any]:
        sources = self._evidence(question, email_ids)
        report = {
            "question": question,
            "summary": (
                f"Found {len(sources)} relevant mailbox source(s). "
                "The findings below are limited to the cited mock inbox records."
                if sources else "No matching inbox evidence was found; no conclusion is asserted."
            ),
            "findings": [
                {"claim": source["excerpt"], "citations": [source["citation"]], "source_subject": source["subject"]}
                for source in sources
            ],
            "sources": sources,
            "limitations": ["Search covers the seeded mock mailbox only.", "A citation identifies a source record, not independent verification."],
        }
        return self._record(9, "deep_research", report)

    def diagnose_operations(self, incident: str) -> dict[str, Any]:
        checks = [
            {"name": "service health", "result": "simulated", "detail": "No live cloud account was contacted."},
            {"name": "deployment events", "result": "simulated", "detail": "Mock event history is not configured."},
            {"name": "rollback readiness", "result": "review_required", "detail": "An operator must verify the target version before rollback."},
        ]
        return self._record(10, "cloud_operations", {
            "incident": incident,
            "environment": "isolated simulation",
            "status": "diagnosed_with_operator_review",
            "checks": checks,
            "recommendation": "Pause the rollout, inspect deployment logs and health probes, then roll back to the last known-good release only after operator confirmation.",
            "recovery_steps": [
                "Capture the deployment identifier and affected service.",
                "Compare health checks and recent deployment events.",
                "Confirm the last known-good version with the service owner.",
                "Perform rollback in the authorized cloud console and verify recovery.",
            ],
            "rollback_available": False,
            "operator_approval_required": True,
        })

    def run_sdlc(self, requirement: str) -> dict[str, Any]:
        requirement = requirement.strip()
        checks = [
            {"name": "requirement captured", "passed": bool(requirement)},
            {"name": "approval gate preserved", "passed": True},
            {"name": "no email-send capability introduced", "passed": True},
            {"name": "audit trail available", "passed": True},
        ]
        return self._record(11, "agentic_sdlc", {
            "requirement": requirement,
            "acceptance_criteria": [
                "The requested behavior is represented in the implementation brief.",
                "Consequential actions pause for a named human reviewer.",
                "The run records inputs, decisions, and outcomes in the audit log.",
            ],
            "design": ["Validate inputs", "Run deterministic checks", "Present results for human review"],
            "generated_tests": checks,
            "tests_passed": all(check["passed"] for check in checks),
            "status": "awaiting_review",
            "note": "This is a deterministic pipeline demonstration; it does not generate, modify, or execute application source code.",
        })

    def evaluate_governance(
        self, action: str, risk_level: str, evidence: str, owner_approved: bool = False, approved_by: str | None = None
    ) -> dict[str, Any]:
        action_terms = set(re.findall(r"[a-z0-9]+", action.casefold()))
        prohibited = (
            {"send", "email"}.issubset(action_terms)
            or "delete" in action_terms
            or {"change", "permissions"}.issubset(action_terms)
            or {"production", "deploy"}.issubset(action_terms)
        )
        approval_required = risk_level == "high" or risk_level == "medium"
        if prohibited:
            decision = "blocked"
            reason = "This demonstration does not authorize external, destructive, or production-changing actions."
        elif approval_required and not owner_approved:
            decision = "approval_required"
            reason = "A named owner must approve this action before it can proceed."
        elif owner_approved and not (approved_by or "").strip():
            decision = "approval_required"
            reason = "Approval must include the reviewing owner's identity."
        else:
            decision = "allowed_for_demo"
            reason = "The action is within the mock-only policy boundary."
        return self._record(12, "governance_evaluation", {
            "action": action,
            "risk_level": risk_level,
            "evidence": evidence,
            "decision": decision,
            "reason": reason,
            "owner_approved": owner_approved and bool((approved_by or "").strip()),
            "approved_by": approved_by if owner_approved and (approved_by or "").strip() else None,
            "rollback_plan": "Restore the prior mock record from its audit snapshot; no external state was changed.",
        })

    def analyze_domain(self, question: str) -> dict[str, Any]:
        sources = self._evidence(question, limit=5)
        return self._record(13, "cse_ai_domain_agent", {
            "question": question,
            "domain": "Computer Science & Engineering (AI)",
            "findings": [
                {"finding": f"{source['category']} message: {source['subject']}", "evidence": source["citation"], "excerpt": source["excerpt"]}
                for source in sources
            ],
            "evidence": sources,
            "recommendation": "Use the cited messages to prepare a faculty decision; do not infer student outcomes or change academic records automatically.",
            "status": "evidence_review_required" if sources else "insufficient_evidence",
        })

    def run_capstone(self, objective: str) -> dict[str, Any]:
        research = self.research(objective)
        sdlc = self.run_sdlc(objective)
        governance = self.evaluate_governance("review capstone findings", "high", "Research citations and generated acceptance checks")
        return self._record(14, "capstone", {
            "objective": objective,
            "status": "waiting_for_approval",
            "stages": [
                {"stage": "research", "record_id": research["id"], "status": "completed", "source_count": len(research["sources"])},
                {"stage": "requirements_and_tests", "record_id": sdlc["id"], "status": sdlc["status"], "tests_passed": sdlc["tests_passed"]},
                {"stage": "safety_evaluation", "record_id": governance["id"], "status": governance["decision"]},
            ],
            "research": research,
            "sdlc": sdlc,
            "governance": governance,
            "approval_required": True,
            "approved_by": None,
        })

    def decide_capstone(self, record_id: str, approved_by: str, approve: bool) -> dict[str, Any]:
        record = next((item for item in self.records if item["id"] == record_id and item["lab"] == 14), None)
        if record is None:
            raise KeyError("Capstone run not found")
        if record["status"] != "waiting_for_approval":
            raise ValueError("Capstone run is not waiting for approval")
        record["status"] = "approved" if approve else "rejected"
        record["approval_required"] = False
        record["approved_by"] = approved_by
        self.connector.save_audit_log({
            "agent": "Human Review",
            "action": "capstone_approve" if approve else "capstone_reject",
            "status": record["status"],
            "details": {"record_id": record_id, "approved_by": approved_by},
        })
        return record

    def history(self, limit: int = 30) -> list[dict[str, Any]]:
        return self.records[:limit]


advanced_labs = AdvancedLabsService()