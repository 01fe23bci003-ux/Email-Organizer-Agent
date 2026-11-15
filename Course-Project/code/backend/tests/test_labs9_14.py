from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_advanced_lab_catalog_covers_labs_9_to_14():
    response = client.get("/api/labs/advanced")

    assert response.status_code == 200
    assert [lab["number"] for lab in response.json()["labs"]] == [9, 10, 11, 12, 13, 14]
    assert client.get("/api/health").json()["labs"] == "1-14"


def test_research_report_cites_matching_mock_mail():
    response = client.post("/api/labs/research", json={"question": "assignment deadline"})

    assert response.status_code == 200
    report = response.json()
    assert report["sources"]
    assert all(source["citation"] == f"[{source['email_id']}]" for source in report["sources"])
    assert all(finding["citations"] for finding in report["findings"])


def test_operations_and_sdlc_are_simulated_and_reviewable():
    operations = client.post("/api/labs/operations/diagnose", json={"incident": "deployment health check failed"})
    sdlc = client.post("/api/labs/sdlc/run", json={"requirement": "Create a reviewable inbox brief"})

    assert operations.status_code == 200
    assert operations.json()["environment"] == "isolated simulation"
    assert operations.json()["rollback_available"] is False
    assert sdlc.status_code == 200
    assert sdlc.json()["tests_passed"] is True
    assert sdlc.json()["status"] == "awaiting_review"


def test_governance_blocks_external_actions_and_requires_named_approval():
    pending = client.post("/api/labs/governance/evaluate", json={
        "action": "review inbox findings", "risk_level": "high", "evidence": "cited messages",
    }).json()
    blocked = client.post("/api/labs/governance/evaluate", json={
        "action": "delete all student emails", "risk_level": "low", "evidence": "draft content",
    }).json()
    send_blocked = client.post("/api/labs/governance/evaluate", json={
        "action": "send email", "risk_level": "low", "evidence": "draft content",
    }).json()
    approved = client.post("/api/labs/governance/evaluate", json={
        "action": "review inbox findings", "risk_level": "high", "evidence": "cited messages",
        "owner_approved": True, "approved_by": "faculty@kletech.ac.in",
    }).json()

    assert pending["decision"] == "approval_required"
    assert blocked["decision"] == "blocked"
    assert send_blocked["decision"] == "blocked"
    assert approved["decision"] == "allowed_for_demo"


def test_domain_agent_returns_cited_cse_ai_mailbox_evidence():
    response = client.post("/api/labs/domain/run", json={"question": "course repository access"})

    assert response.status_code == 200
    result = response.json()
    assert result["domain"] == "Computer Science & Engineering (AI)"
    assert result["evidence"]
    assert all(item["evidence"].startswith("[em-") for item in result["findings"])


def test_capstone_pauses_for_named_approval_and_records_decision():
    response = client.post("/api/labs/capstone/run", json={"objective": "faculty assignment deadline brief"})

    assert response.status_code == 200
    record = response.json()
    assert record["status"] == "waiting_for_approval"
    assert [stage["stage"] for stage in record["stages"]] == ["research", "requirements_and_tests", "safety_evaluation"]

    approved = client.post(
        f"/api/labs/capstone/{record['id']}/approve",
        json={"approved_by": "faculty@kletech.ac.in"},
    )
    repeated = client.post(
        f"/api/labs/capstone/{record['id']}/approve",
        json={"approved_by": "faculty@kletech.ac.in"},
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert repeated.status_code == 409