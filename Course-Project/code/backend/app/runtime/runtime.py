from datetime import datetime, timezone
from threading import RLock
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.connectors.email_connector import EmailConnector, connector


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentStep(BaseModel):
    id: str
    agent_name: str
    status: Literal["running", "completed", "failed"]
    input_summary: str
    output_summary: str = ""
    email_id: str | None = None
    started_at: str
    completed_at: str | None = None
    duration_ms: float | None = None
    error: str | None = None


class AgentRun(BaseModel):
    id: str
    plan_id: str
    email_ids: list[str]
    status: Literal["running", "checkpointed", "waiting_for_approval", "completed", "rejected", "failed"] = "running"
    started_at: str
    completed_at: str | None = None
    current_node: str = "START"
    retry_count: int = 0
    requires_approval: bool = False
    approved_by: str | None = None
    checkpoint_data: dict[str, Any] = Field(default_factory=dict)
    steps: list[AgentStep] = Field(default_factory=list)


class AgentRuntime:
    def __init__(self, data_connector: EmailConnector = connector) -> None:
        self.connector = data_connector
        self.runs: dict[str, AgentRun] = {}
        self.lock = RLock()

    def create_run(self, plan_id: str, email_ids: list[str]) -> AgentRun:
        run = AgentRun(id=f"run_{uuid4().hex[:12]}", plan_id=plan_id, email_ids=email_ids, started_at=timestamp())
        with self.lock:
            self.runs[run.id] = run
        self._audit(run.id, "Coordinator", "create_run", "success", {"email_count": len(email_ids)})
        return run

    def get_run(self, run_id: str) -> AgentRun:
        with self.lock:
            run = self.runs.get(run_id)
            if run is None:
                raise KeyError(f"Run not found: {run_id}")
            return run

    def list_runs(self) -> list[AgentRun]:
        with self.lock:
            return list(reversed(list(self.runs.values())))

    def begin_step(self, run_id: str, agent_name: str, input_summary: str, email_id: str | None = None) -> str:
        step_id = f"step_{uuid4().hex[:10]}"
        step = AgentStep(
            id=step_id,
            agent_name=agent_name,
            status="running",
            input_summary=input_summary,
            email_id=email_id,
            started_at=timestamp(),
        )
        with self.lock:
            run = self.get_run(run_id)
            run.current_node = agent_name
            run.steps.append(step)
        self._audit(run_id, agent_name, "start_step", "running", {"email_id": email_id, "input": input_summary})
        return step_id

    def finish_step(self, run_id: str, step_id: str, output_summary: str, error: str | None = None) -> AgentStep:
        with self.lock:
            run = self.get_run(run_id)
            step = next((item for item in run.steps if item.id == step_id), None)
            if step is None:
                raise KeyError(f"Step not found: {step_id}")
            step.completed_at = timestamp()
            step.output_summary = output_summary
            step.error = error
            step.status = "failed" if error else "completed"
            step.duration_ms = max(0.0, (datetime.fromisoformat(step.completed_at) - datetime.fromisoformat(step.started_at)).total_seconds() * 1000)
        self._audit(run_id, step.agent_name, "finish_step", step.status, {"output": output_summary, "error": error})
        return step

    def checkpoint(self, run_id: str, node: str, data: dict[str, Any]) -> None:
        with self.lock:
            run = self.get_run(run_id)
            run.checkpoint_data = {"node": node, "data": data, "saved_at": timestamp()}
            run.current_node = node
            run.status = "checkpointed"
        self._audit(run_id, "Runtime", "checkpoint", "success", {"node": node})

    def resume(self, run_id: str) -> dict[str, Any]:
        with self.lock:
            run = self.get_run(run_id)
            if run.status != "checkpointed":
                raise ValueError("Only checkpointed runs can be resumed")
            checkpoint = run.checkpoint_data
            run.status = "running"
        self._audit(run_id, "Runtime", "resume", "success", {"node": checkpoint.get("node")})
        return checkpoint

    def record_retry(self, run_id: str, node: str, reason: str) -> int:
        with self.lock:
            run = self.get_run(run_id)
            run.retry_count += 1
            run.current_node = node
            retry_count = run.retry_count
        self._audit(run_id, "Runtime", "retry", "success", {"node": node, "reason": reason, "retry_count": retry_count})
        return retry_count

    def wait_for_approval(self, run_id: str) -> AgentRun:
        with self.lock:
            run = self.get_run(run_id)
            run.status = "waiting_for_approval"
            run.current_node = "HUMAN_REVIEW"
            run.requires_approval = True
        self._audit(run_id, "Human Review", "approval_gate", "waiting", {"email_ids": run.email_ids})
        return run

    def approve(self, run_id: str, approved_by: str) -> AgentRun:
        with self.lock:
            run = self.get_run(run_id)
            if run.status != "waiting_for_approval":
                raise ValueError("Run is not waiting for human approval")
            run.status = "completed"
            run.current_node = "END"
            run.completed_at = timestamp()
            run.requires_approval = False
            run.approved_by = approved_by
        self._audit(run_id, "Human Review", "approve_run", "approved", {"approved_by": approved_by})
        return run

    def reject(self, run_id: str, rejected_by: str) -> AgentRun:
        with self.lock:
            run = self.get_run(run_id)
            if run.status != "waiting_for_approval":
                raise ValueError("Run is not waiting for human approval")
            run.status = "rejected"
            run.current_node = "END"
            run.completed_at = timestamp()
            run.requires_approval = False
        self._audit(run_id, "Human Review", "reject_run", "rejected", {"rejected_by": rejected_by})
        return run

    def authorize_archive(self, run_id: str) -> bool:
        with self.lock:
            run = self.get_run(run_id)
            if run.status != "completed" or not run.approved_by:
                raise PermissionError("Archiving consequential results requires mailbox-owner approval")
        self._audit(run_id, "ArchiveAgent", "authorize_archive", "success", {"approved_by": run.approved_by})
        return True

    def _audit(self, run_id: str, agent: str, action: str, status: str, details: dict[str, Any]) -> None:
        self.connector.save_audit_log(
            {"timestamp": timestamp(), "run_id": run_id, "agent": agent, "action": action, "status": status, "details": details}
        )