import json
import re
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any

from app.data.mock_data import MOCK_CONTACTS, MOCK_EMAILS, MOCK_PREVIOUS_REPLIES
from app.models.email import Contact, EmailMessage, PriorReply


class RunMemory:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}

    def start(self, run_id: str) -> dict[str, Any]:
        state = {
            "run_id": run_id,
            "current_email_id": None,
            "agent_results": {},
            "current_draft": None,
        }
        self.sessions[run_id] = state
        return state

    def update(self, run_id: str, **values: Any) -> dict[str, Any]:
        if run_id not in self.sessions:
            raise KeyError(f"No active run state for {run_id}")
        self.sessions[run_id].update(values)
        return self.sessions[run_id]


class MemoryStore:
    """SQLite long-term memory; short-lived orchestration state stays in RunMemory."""

    def __init__(self, database_path: str | Path = ":memory:", seed: bool = True) -> None:
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = RLock()
        self._initialize()
        if seed:
            self._seed_if_empty()

    def _initialize(self) -> None:
        with self.lock, self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS contacts (
                    email TEXT PRIMARY KEY, display_name TEXT NOT NULL, category TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS prior_replies (
                    contact_email TEXT NOT NULL, thread_id TEXT NOT NULL, body TEXT NOT NULL,
                    created_at TEXT NOT NULL, PRIMARY KEY (contact_email, thread_id)
                );
                CREATE TABLE IF NOT EXISTS email_history (
                    id TEXT PRIMARY KEY, sender TEXT NOT NULL, subject TEXT NOT NULL,
                    body TEXT NOT NULL, category TEXT NOT NULL, tags TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS drafts (
                    id TEXT PRIMARY KEY, email_id TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY, payload TEXT NOT NULL
                );
                """
            )

    def _seed_if_empty(self) -> None:
        with self.lock:
            count = self.connection.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        if count:
            return
        for contact in MOCK_CONTACTS:
            self.remember_contact(contact)
        for reply in MOCK_PREVIOUS_REPLIES:
            self.remember_reply(reply)
        for email in MOCK_EMAILS:
            self.remember_email(email)

    def remember_contact(self, contact: Contact) -> None:
        with self.lock, self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO contacts VALUES (?, ?, ?)",
                (contact.email.casefold(), contact.display_name, contact.category),
            )

    def remember_reply(self, reply: PriorReply) -> None:
        with self.lock, self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO prior_replies VALUES (?, ?, ?, ?)",
                (reply.contact_email.casefold(), reply.thread_id, reply.body, reply.created_at),
            )

    def remember_email(self, email: EmailMessage) -> None:
        with self.lock, self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO email_history VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    email.id,
                    email.sender.casefold(),
                    email.subject,
                    email.body,
                    email.sender_category,
                    json.dumps(email.tags),
                    email.timestamp,
                ),
            )

    def retrieve_contact(self, sender: str) -> Contact | None:
        with self.lock:
            row = self.connection.execute(
                "SELECT email, display_name, category FROM contacts WHERE email = ?",
                (sender.casefold(),),
            ).fetchone()
        return Contact(**dict(row)) if row else None

    def retrieve_previous_replies(self, email: EmailMessage) -> list[PriorReply]:
        with self.lock:
            rows = self.connection.execute(
                "SELECT contact_email, thread_id, body, created_at FROM prior_replies WHERE contact_email = ? ORDER BY created_at DESC",
                (email.sender.casefold(),),
            ).fetchall()
        return [PriorReply(**dict(row)) for row in rows]

    def retrieve_similar_emails(self, email: EmailMessage, limit: int = 5) -> list[dict[str, Any]]:
        query_terms = self._terms(f"{email.subject} {email.body} {' '.join(email.tags)}")
        with self.lock:
            rows = self.connection.execute(
                "SELECT id, sender, subject, body, category, tags, timestamp FROM email_history WHERE id != ?",
                (email.id,),
            ).fetchall()
        scored: list[tuple[int, sqlite3.Row]] = []
        for row in rows:
            row_terms = self._terms(f"{row['subject']} {row['body']} {row['tags']}")
            overlap = len(query_terms & row_terms)
            if overlap:
                scored.append((overlap, row))
        scored.sort(key=lambda item: (-item[0], item[1]["timestamp"]))
        return [
            {**dict(row), "tags": json.loads(row["tags"]), "similarity": score / max(1, len(query_terms))}
            for score, row in scored[:limit]
        ]

    def save_draft_record(self, draft: dict[str, Any]) -> None:
        with self.lock, self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO drafts VALUES (?, ?, ?, ?)",
                (draft["id"], draft["email_id"], draft["status"], json.dumps(draft)),
            )

    def get_draft_record(self, draft_id: str) -> dict[str, Any] | None:
        with self.lock:
            row = self.connection.execute("SELECT payload FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def list_draft_records(self) -> list[dict[str, Any]]:
        with self.lock:
            rows = self.connection.execute("SELECT payload FROM drafts ORDER BY rowid DESC").fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def save_audit_record(self, entry: dict[str, Any]) -> None:
        with self.lock, self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO audit_logs VALUES (?, ?)",
                (entry["id"], json.dumps(entry, default=str)),
            )

    def list_audit_records(self) -> list[dict[str, Any]]:
        with self.lock:
            rows = self.connection.execute("SELECT payload FROM audit_logs ORDER BY rowid DESC").fetchall()
        return [json.loads(row["payload"]) for row in rows]

    @staticmethod
    def _terms(value: str) -> set[str]:
        return {term for term in re.findall(r"[a-z0-9]+", value.casefold()) if len(term) > 2}

    def close(self) -> None:
        with self.lock:
            self.connection.close()