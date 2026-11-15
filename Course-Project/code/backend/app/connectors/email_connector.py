from pathlib import Path
from threading import RLock
from typing import Any, Protocol
from uuid import uuid4

from app.data.mock_data import MOCK_CALENDAR, MOCK_CONTACTS, MOCK_EMAILS, MOCK_PREVIOUS_REPLIES, MOCK_TASKS
from app.memory.store import MemoryStore
from app.models.email import Contact, EmailMessage, PriorReply


class EmailConnector(Protocol):
    def read_inbox(self) -> list[dict[str, Any]]: ...
    def read_email(self, email_id: str) -> dict[str, Any] | None: ...
    def search_emails(self, query: str) -> list[dict[str, Any]]: ...
    def read_contacts(self) -> list[dict[str, Any]]: ...
    def read_previous_replies(self, sender: str | None = None) -> list[dict[str, Any]]: ...
    def read_calendar(self) -> list[dict[str, Any]]: ...
    def read_tasks(self) -> list[dict[str, Any]]: ...
    def save_draft(self, email_id: str, body: str, **metadata: Any) -> dict[str, Any]: ...
    def save_audit_log(self, entry: dict[str, Any]) -> dict[str, Any]: ...


class MockEmailConnector:
    """Governed mailbox boundary; replace this adapter for Gmail/Calendar later."""

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self.memory = MemoryStore(database_path)
        self.lock = RLock()

    def read_inbox(self) -> list[dict[str, Any]]:
        return [email.model_dump() for email in MOCK_EMAILS]

    def read_email(self, email_id: str) -> dict[str, Any] | None:
        email = next((item for item in MOCK_EMAILS if item.id == email_id), None)
        return email.model_dump() if email else None

    def search_emails(self, query: str) -> list[dict[str, Any]]:
        term = query.casefold()
        return [
            item for item in self.read_inbox()
            if term in f"{item['sender']} {item['subject']} {item['body']} {' '.join(item['tags'])}".casefold()
        ]

    def read_contacts(self) -> list[dict[str, Any]]:
        return [contact.model_dump() for contact in MOCK_CONTACTS]

    def read_contact(self, sender: str) -> Contact | None:
        return self.memory.retrieve_contact(sender)

    def read_previous_replies(self, sender: str | None = None) -> list[dict[str, Any]]:
        if sender:
            email = next((item for item in MOCK_EMAILS if item.sender.casefold() == sender.casefold()), None)
            replies = self.memory.retrieve_previous_replies(email) if email else []
        else:
            replies = [PriorReply.model_validate(reply) for reply in MOCK_PREVIOUS_REPLIES]
        return [reply.model_dump() for reply in replies]

    def read_similar_emails(self, email_id: str, limit: int = 5) -> list[dict[str, Any]]:
        email = next((item for item in MOCK_EMAILS if item.id == email_id), None)
        return self.memory.retrieve_similar_emails(email, limit) if email else []

    def read_calendar(self) -> list[dict[str, Any]]:
        return [event.model_dump() for event in MOCK_CALENDAR]

    def read_tasks(self) -> list[dict[str, Any]]:
        return [task.model_dump() for task in MOCK_TASKS]

    def save_draft(self, email_id: str, body: str, **metadata: Any) -> dict[str, Any]:
        if self.read_email(email_id) is None:
            raise KeyError(f"Email not found: {email_id}")
        draft = {
            "id": metadata.pop("id", f"draft_{uuid4().hex[:10]}"),
            "email_id": email_id,
            "body": body,
            **metadata,
            "status": "draft",
        }
        self.memory.save_draft_record(draft)
        return draft.copy()

    def read_drafts(self) -> list[dict[str, Any]]:
        return self.memory.list_draft_records()

    def read_draft(self, draft_id: str) -> dict[str, Any] | None:
        return self.memory.get_draft_record(draft_id)

    def update_draft(self, draft_id: str, **updates: Any) -> dict[str, Any]:
        with self.lock:
            draft = self.memory.get_draft_record(draft_id)
            if draft is None:
                raise KeyError(f"Draft not found: {draft_id}")
            if draft["status"] != "draft":
                raise ValueError("Only unreviewed drafts can be changed")
            draft.update(updates)
            self.memory.save_draft_record(draft)
            return draft.copy()

    def save_audit_log(self, entry: dict[str, Any]) -> dict[str, Any]:
        record = {"id": f"audit_{uuid4().hex[:10]}", **entry}
        self.memory.save_audit_record(record)
        return record.copy()

    def read_audit_logs(self) -> list[dict[str, Any]]:
        return self.memory.list_audit_records()


_database_path = Path(__file__).resolve().parents[2] / "data" / "email_memory.sqlite3"
connector: EmailConnector = MockEmailConnector(_database_path)