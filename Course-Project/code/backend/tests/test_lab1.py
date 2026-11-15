from fastapi.testclient import TestClient

from app.agents.lab1_planner import EmailOrganizerPlannerAgent
from app.main import app

client = TestClient(app)


def test_plan_review_revision_and_lock_gate():
    created = client.post(
        "/api/agent/plan", json={"request": "Organize my inbox and prepare replies"}
    )
    assert created.status_code == 200
    plan = created.json()
    assert plan["status"] == "review"
    assert plan["approval_required"] is True
    assert plan["clarification_questions"]
    assert set(plan["requirements"]) == {
        "mailbox_scope",
        "priority_categories",
        "date_range",
        "standard_response_library_available",
    }
    assert plan["iteration_log"]

    revised = client.put(
        f"/api/agent/plan/{plan['id']}",
        json={
            "goal": "Organize my college inbox",
            "steps": ["Read emails", "Prepare drafts"],
            "merge_vendor_into_other": True,
        },
    )
    assert revised.status_code == 200
    assert revised.json()["steps"] == ["Read emails", "Prepare drafts"]
    assert "vendor" not in revised.json()["categories"]
    assert "other" in revised.json()["categories"]

    locked = client.post(f"/api/agent/plan/{plan['id']}/lock")
    assert locked.status_code == 200
    assert locked.json()["status"] == "locked"

    rejected_revision = client.put(
        f"/api/agent/plan/{plan['id']}",
        json={"goal": "Change locked plan", "steps": ["Do something else"]},
    )
    assert rejected_revision.status_code == 409


def test_missing_plan_returns_404():
    response = client.post("/api/agent/plan/not-a-plan/lock")
    assert response.status_code == 404


def test_planner_asks_until_requirements_are_filled_then_revises_in_place():
    agent = EmailOrganizerPlannerAgent()
    plan = agent.run()
    assert agent.clarifying_questions_asked == 4
    assert agent.next_step() == ("generate_plan", None)
    original_steps = plan["steps"]

    agent.revise({"merge_categories": {"vendor": "other"}})

    assert agent.plan is plan
    assert plan["steps"] == original_steps
    assert "vendor" not in plan["categories"]
    assert len(agent.log) == 6
