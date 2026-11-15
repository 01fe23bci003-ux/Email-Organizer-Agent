from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_locked_plan_runs_parallel_then_waits_for_owner_approval():
    plan_response = client.post(
        "/api/agent/plan", json={"request": "Triage the faculty inbox and prepare reply drafts"}
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()
    assert client.get("/api/emails").status_code == 200

    blocked = client.post("/api/agent/run", json={"plan_id": plan["id"], "email_ids": ["em-001"]})
    assert blocked.status_code == 409

    locked = client.post(f"/api/agent/plan/{plan['id']}/lock")
    assert locked.status_code == 200
    response = client.post(
        "/api/agent/run",
        json={"plan_id": plan["id"], "email_ids": ["em-001", "em-002", "em-003"], "max_workers": 3},
    )
    assert response.status_code == 200
    run_payload = response.json()
    run_id = run_payload["run"]["id"]
    assert run_payload["run"]["status"] == "waiting_for_approval"
    assert len(run_payload["results"]) == 3
    assert run_payload["merge"]["processed_count"] == 3
    assert all(result["archived"] is False for result in run_payload["results"])

    detail = client.get(f"/api/agent/runs/{run_id}").json()
    assert detail["run"]["requires_approval"] is True
    assert detail["merge"]["processed_count"] == 3
    assert detail["merge"]["max_observed_workers"] >= 1

    approved = client.post(
        f"/api/agent/runs/{run_id}/approve", json={"approved_by": "faculty@kletech.ac.in"}
    )
    assert approved.status_code == 200
    assert approved.json()["run"]["status"] == "completed"
    assert all(result["archived"] for result in approved.json()["results"])
    assert all(result["draft_reply"]["status"] == "draft" for result in approved.json()["results"])
    assert client.get("/api/audit-logs").status_code == 200