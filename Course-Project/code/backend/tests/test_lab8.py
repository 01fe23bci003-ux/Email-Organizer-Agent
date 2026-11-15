import asyncio
from time import sleep

from app.connectors.email_connector import MockEmailConnector
from app.graph.email_graph import EmailAgentGraph
from app.runtime.runtime import AgentRuntime


def locked_plan():
    return {
        "id": "plan-lab8",
        "status": "locked",
        "categories": ["Student", "Faculty", "Administration", "Collaborator", "Vendor", "Other"],
        "requirements": {"priority_categories": ["URGENT", "HIGH", "MEDIUM", "LOW"]},
    }


class ObservableParallelGraph(EmailAgentGraph):
    def process_email(self, run_id, email_id, plan):
        sleep(0.025)
        return super().process_email(run_id, email_id, plan)


def test_parallel_fan_out_fan_in_returns_all_schema_valid_results():
    data_connector = MockEmailConnector()
    graph = ObservableParallelGraph(data_connector, AgentRuntime(data_connector))
    requested = [f"em-{number:03}" for number in range(1, 21)]
    run, results, merge = asyncio.run(graph.run_parallel(locked_plan(), requested, max_workers=4))

    assert run.status == "waiting_for_approval"
    assert [result.email_id for result in results] == requested
    assert all(result.draft_reply.status == "draft" for result in results)
    assert all(result.validation.attempts <= 3 for result in results)
    assert merge["processed_count"] == 20
    assert merge["failed_email_ids"] == []
    assert merge["max_observed_workers"] > 1
    assert merge["priority_counts"]["URGENT"] >= 1
    assert "locked request order" in merge["merge_rule"]
    assert all(result.archived is False for result in results)
    data_connector.memory.close()


def test_parallel_batch_rejects_unlocked_plan_and_duplicate_ids():
    data_connector = MockEmailConnector()
    graph = EmailAgentGraph(data_connector, AgentRuntime(data_connector))
    unlocked = {**locked_plan(), "status": "review"}
    try:
        asyncio.run(graph.run_parallel(unlocked, ["em-001"]))
        assert False, "unlocked plan should be rejected"
    except PermissionError:
        pass
    try:
        asyncio.run(graph.run_parallel(locked_plan(), ["em-001", "em-001"]))
        assert False, "duplicate IDs should be rejected"
    except ValueError:
        pass
    data_connector.memory.close()