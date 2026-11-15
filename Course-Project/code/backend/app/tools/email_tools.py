from typing import Any, Callable

from app.connectors.email_connector import connector


def read_inbox_threads() -> list[dict[str, Any]]:
    return connector.read_inbox()


def read_contacts_prior_replies() -> dict[str, list[dict[str, Any]]]:
    return {
        "contacts": connector.read_contacts(),
        "previous_replies": connector.read_previous_replies(),
    }


def read_email(email_id: str) -> dict[str, Any] | None:
    return connector.read_email(email_id)


def search_emails(query: str) -> list[dict[str, Any]]:
    return connector.search_emails(query)


def read_contacts() -> list[dict[str, Any]]:
    return connector.read_contacts()


def get_previous_replies() -> list[dict[str, Any]]:
    return connector.read_previous_replies()


def get_calendar_events() -> list[dict[str, Any]]:
    return connector.read_calendar()


def get_tasks() -> list[dict[str, Any]]:
    return connector.read_tasks()


def calculator(operation: str, values: list[float]) -> float:
    if not values:
        raise ValueError("values must not be empty")
    if operation == "sum":
        return float(sum(values))
    if operation == "average":
        return float(sum(values) / len(values))
    if operation == "count":
        return float(len(values))
    raise ValueError(f"Unsupported calculator operation: {operation}")


def compute_verified_priority(
    emails: list[dict[str, Any]], contacts: list[dict[str, Any]]
) -> dict[str, Any]:
    contact_categories = {contact["email"].casefold(): contact["category"] for contact in contacts}
    priorities = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "URGENT": 4}
    checked: list[dict[str, Any]] = []
    unmatched: list[str] = []
    for email in emails:
        verified_category = contact_categories.get(email["sender"].casefold())
        category_verified = verified_category is not None and verified_category.casefold() == email["sender_category"].casefold()
        if not category_verified:
            unmatched.append(email["sender"])
        checked.append(
            {
                "email_id": email["id"],
                "sender": email["sender"],
                "claimed_category": email["sender_category"],
                "verified_category": verified_category,
                "category_verified": category_verified,
                "priority": email["priority"],
                "priority_score": priorities.get(email["priority"], 0),
            }
        )
    return {"valid": not unmatched, "emails": checked, "unmatched_senders": unmatched}


TOOLS: dict[str, Callable[..., Any]] = {
    "read_inbox_threads": read_inbox_threads,
    "read_email": read_email,
    "search_emails": search_emails,
    "read_contacts": read_contacts,
    "read_contacts_prior_replies": read_contacts_prior_replies,
    "get_previous_replies": get_previous_replies,
    "get_calendar_events": get_calendar_events,
    "get_tasks": get_tasks,
    "calculator": calculator,
    "compute_verified_priority": compute_verified_priority,
}


class EmailOrganizerToolAgent:
    def __init__(self) -> None:
        self.trace: list[dict[str, Any]] = []

    def _call(self, tool_name: str, reason: str, **inputs: Any) -> Any:
        if tool_name not in TOOLS:
            raise KeyError(f"Unknown tool: {tool_name}")
        output = TOOLS[tool_name](**inputs) if inputs else TOOLS[tool_name]()
        self.trace.append(
            {"tool": tool_name, "reason": reason, "input": inputs, "output": output}
        )
        connector.save_audit_log(
            {
                "agent": "EmailOrganizerToolAgent",
                "action": tool_name,
                "reason": reason,
                "input": inputs,
                "output": output,
                "status": "success",
            }
        )
        return output

    def verified_priority_report(self) -> dict[str, Any]:
        emails = self._call("read_inbox_threads", "Load inbox records to triage")
        context = self._call(
            "read_contacts_prior_replies", "Verify sender categories and retrieve thread history"
        )
        checked = self._call(
            "compute_verified_priority",
            "Cross-check each claimed category against the contact store",
            emails=emails,
            contacts=context["contacts"],
        )
        verified_scores = [row["priority_score"] for row in checked["emails"] if row["category_verified"]]
        total = self._call("calculator", "Aggregate verified priority scores", operation="sum", values=verified_scores)
        average = self._call("calculator", "Calculate mean verified priority score", operation="average", values=verified_scores)
        return {
            "valid": checked["valid"],
            "email_count": len(emails),
            "verified_count": len(verified_scores),
            "unmatched_senders": checked["unmatched_senders"],
            "priority_score_total": total,
            "priority_score_average": average,
            "emails": checked["emails"],
        }