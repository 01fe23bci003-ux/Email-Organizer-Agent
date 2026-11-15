import pytest

from app.connectors.email_connector import MockEmailConnector
from app.graph.email_graph import MAX_RETRIES, NODE_GRAPH, EmailAgentGraph
from app.runtime.runtime import AgentRuntime


def locked_plan():
    return {
        "id": "plan-lab7",
        "status": "locked",
        "categories": ["Student", "Faculty", "Administration", "Collaborator", "Vendor", "Other"],
        "requirements": {"priority_categories": ["URGENT", "HIGH", "MEDIUM", "LOW"]},
    }


def test_explicit_graph_validates_and_waits_for_owner_before_archive():
    data_connector = MockEmailConnector()
    runtime = AgentRuntime(data_connector)
    graph = EmailAgentGraph(data_connector, runtime)
    run, results = graph.run_serial(locked_plan(), ["em-001"])

    assert [node for node in NODE_GRAPH["START"]] == ["INGESTION_CLASSIFICATION"]
    assert NODE_GRAPH["VALIDATION"] == ["INGESTION_CLASSIFICATION", "HUMAN_REVIEW"]
    assert len(results) == 1 and results[0].validation.passed
    assert run.status == "waiting_for_approval"
    assert results[0].draft_reply.status == "draft"
    assert results[0].archived is False

    archived = graph.approve_run(run.id, "faculty@kletech.ac.in")
    assert archived[0].archived is True
    assert run.status == "completed"
    data_connector.memory.close()


def test_graph_requires_locked_plan_and_bounds_validation_retries():
    data_connector = MockEmailConnector()
    graph = EmailAgentGraph(data_connector, AgentRuntime(data_connector), max_retries=MAX_RETRIES)
    with pytest.raises(PermissionError):
        graph.run_serial({**locked_plan(), "status": "review"}, ["em-001"])

    run = graph.runtime.create_run("plan-lab7", ["em-001"])
    result = graph.process_email(run.id, "em-001", {**locked_plan(), "categories": ["Faculty"]})
    assert result.validation.attempts == MAX_RETRIES + 1
    assert run.retry_count == MAX_RETRIES
    assert result.validation.requires_human_review is True
    data_connector.memory.close()