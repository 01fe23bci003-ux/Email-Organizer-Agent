import pytest

from app.connectors.email_connector import MockEmailConnector
from app.runtime.runtime import AgentRuntime


def test_runtime_tracks_steps_audit_checkpoint_and_resume():
    data_connector = MockEmailConnector()
    runtime = AgentRuntime(data_connector)
    run = runtime.create_run("plan-test", ["em-001"])
    step_id = runtime.begin_step(run.id, "PriorityAgent", "Score em-001", "em-001")
    step = runtime.finish_step(run.id, step_id, "HIGH / score 70")
    runtime.checkpoint(run.id, "DRAFT_REPLY", {"email_id": "em-001"})
    checkpoint = runtime.resume(run.id)

    assert run.status == "running"
    assert step.status == "completed" and step.duration_ms is not None
    assert checkpoint["data"]["email_id"] == "em-001"
    assert {entry["action"] for entry in data_connector.read_audit_logs()} >= {"create_run", "start_step", "finish_step", "checkpoint", "resume"}
    data_connector.memory.close()


def test_runtime_holds_hard_approval_gate():
    data_connector = MockEmailConnector()
    runtime = AgentRuntime(data_connector)
    run = runtime.create_run("plan-test", ["em-001"])
    runtime.wait_for_approval(run.id)

    assert run.status == "waiting_for_approval"
    assert run.requires_approval is True
    with pytest.raises(PermissionError):
        runtime.authorize_archive(run.id)
    approved = runtime.approve(run.id, "owner@example.edu")
    assert approved.status == "completed"
    assert approved.approved_by == "owner@example.edu"
    assert runtime.authorize_archive(run.id) is True
    data_connector.memory.close()