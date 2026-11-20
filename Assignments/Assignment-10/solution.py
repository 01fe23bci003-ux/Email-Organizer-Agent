from __future__ import annotations

from typing import Any


INCIDENTS: list[dict[str, Any]] = [
    {
        "id": "deploy-500",
        "title": "Failed application deployment",
        "severity": "CRITICAL",
        "logs": ["health check failed after deploy", "error rate exceeded threshold"],
        "deploy_history": ["v1.7 healthy", "v1.8 failed"],
        "metrics": {"error_rate": "18%", "healthy_pods": 1},
        "proposed_action": "rollback_deployment",
    },
    {
        "id": "db-pool-501",
        "title": "Database connection-pool exhaustion",
        "severity": "WARN",
        "logs": ["connection pool at maximum", "requests queued for connections"],
        "deploy_history": ["v2.3 healthy"],
        "metrics": {"pool_used": "100%", "queue_depth": 12},
        "proposed_action": "restart_single_pod",
    },
]


def remediate(incident: dict[str, Any]) -> tuple[str, bool, bool]:
    action = incident["proposed_action"]
    if action == "restart_single_pod" and incident["severity"] == "WARN":
        return "executed automatically (low risk)", True, False
    if action == "rollback_deployment":
        return "approval requested", False, True
    return "manual review required", False, True


def main() -> None:
    executed_actions: list[str] = []
    for incident in INCIDENTS:
        assert incident["logs"] and incident["deploy_history"] and incident["metrics"]
        message, executed, approval_requested = remediate(incident)
        print(
            f"incident {incident['id']}: severity={incident['severity']}; "
            f"logs={len(incident['logs'])}; deploys={len(incident['deploy_history'])}; "
            f"metrics={len(incident['metrics'])}"
        )
        print(f"  logs: {incident['logs']}")
        print(f"  deploy history: {incident['deploy_history']}")
        print(f"  metrics: {incident['metrics']}")
        print(f"action {incident['proposed_action']}: {message}")
        if executed:
            executed_actions.append(incident["proposed_action"])
        if incident["proposed_action"] == "rollback_deployment":
            assert approval_requested and not executed

    assert "restart_single_pod" in executed_actions
    assert "rollback_deployment" not in executed_actions
    print("rollback auto-execution assertion: passed")


if __name__ == "__main__":
    main()
