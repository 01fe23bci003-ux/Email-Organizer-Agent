from app.data.mock_data import MOCK_EMAILS
from app.memory.store import MemoryStore, RunMemory


def test_short_term_run_state_is_separate_and_ephemeral():
    memory = RunMemory()
    state = memory.start("run-test")
    memory.update("run-test", current_email_id="em-001", current_draft="review me")

    assert state["current_email_id"] == "em-001"
    assert state["current_draft"] == "review me"
    assert memory.sessions["run-test"]["agent_results"] == {}


def test_long_term_sqlite_retrieval_finds_contact_reply_and_similar_threads(tmp_path):
    database = tmp_path / "memory.sqlite3"
    store = MemoryStore(database)
    email = MOCK_EMAILS[0]
    contact = store.retrieve_contact(email.sender)
    replies = store.retrieve_previous_replies(email)
    similar = store.retrieve_similar_emails(email)
    store.close()

    reopened = MemoryStore(database, seed=False)
    assert contact is not None and contact.category == "Student"
    assert replies and "deadline" in replies[0].body
    assert similar and all(item["similarity"] > 0 for item in similar)
    assert reopened.retrieve_contact(email.sender) == contact
    reopened.close()