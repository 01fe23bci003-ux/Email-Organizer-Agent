from app.connectors.email_connector import MockEmailConnector


def test_single_connector_governs_mailbox_memory_and_draft_writes(tmp_path):
    database = tmp_path / "connector.sqlite3"
    connector = MockEmailConnector(database)
    emails = connector.read_inbox()
    email = connector.read_email("em-001")
    similar = connector.read_similar_emails("em-001")
    draft = connector.save_draft("em-001", "Please see the updated deadline.", confidence=0.7)
    audit = connector.save_audit_log({"agent": "TestAgent", "action": "save_draft", "status": "success"})

    assert len(emails) == 20
    assert email and email["id"] == "em-001"
    assert similar
    assert draft["status"] == "draft"
    assert draft["id"] in [item["id"] for item in connector.read_drafts()]
    assert audit["agent"] == "TestAgent"
    assert not hasattr(connector, "send_email")
    connector.memory.close()

    reopened = MockEmailConnector(database)
    assert reopened.read_draft(draft["id"])["body"] == draft["body"]
    assert any(entry["id"] == audit["id"] for entry in reopened.read_audit_logs())
    reopened.memory.close()