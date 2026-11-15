from app.data.mock_data import MOCK_EMAILS
from app.tools.email_tools import EmailOrganizerToolAgent, calculator, read_email, search_emails


def test_mock_inbox_has_twenty_typed_emails_and_lookup_tools_work():
    assert len(MOCK_EMAILS) == 20
    assert read_email("em-001")["sender_category"] == "Student"
    assert len(search_emails("urgent")) >= 1
    assert calculator("sum", [1, 2, 3]) == 6


def test_tool_agent_logs_tool_calls_and_verifies_sender_categories():
    agent = EmailOrganizerToolAgent()
    report = agent.verified_priority_report()

    assert report["valid"] is True
    assert report["email_count"] == 20
    assert report["verified_count"] == 20
    assert [item["tool"] for item in agent.trace] == [
        "read_inbox_threads",
        "read_contacts_prior_replies",
        "compute_verified_priority",
        "calculator",
        "calculator",
    ]
    assert all(item["reason"] and "output" in item for item in agent.trace)