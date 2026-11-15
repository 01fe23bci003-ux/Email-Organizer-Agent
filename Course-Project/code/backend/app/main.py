from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

from app.agents.advanced_labs import advanced_labs
from app.agents.lab1_planner import EmailOrganizerPlannerAgent
from app.connectors.email_connector import connector
from app.graph.email_graph import EmailAgentGraph
from app.models.email import CalendarEvent, Contact, EmailMessage, PriorReply
from app.skills.email_skills import (
    calculate_priority,
    classify_email,
    draft_reply,
    extract_action_items,
    prepare_calendar_suggestion,
    prepare_follow_up,
)

app = FastAPI(title="Email Organizer Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    request: str = Field(min_length=3, max_length=1000)


class PlanRevision(BaseModel):
    goal: str = Field(min_length=3, max_length=300)
    steps: list[str] = Field(min_length=1, max_length=12)
    merge_vendor_into_other: bool = False


class PlannerRequirements(BaseModel):
    mailbox_scope: str
    priority_categories: list[str]
    date_range: str
    standard_response_library_available: bool


class ExecutionPlan(BaseModel):
    id: str
    request: str
    goal: str
    clarification_questions: list[str]
    steps: list[str]
    requirements: PlannerRequirements
    categories: list[str]
    iteration_log: list[dict[str, str]]
    approval_required: bool = True
    status: str = "review"


plans: dict[str, ExecutionPlan] = {}
planner_instances: dict[str, EmailOrganizerPlannerAgent] = {}
agent_graph = EmailAgentGraph(connector)


class AgentRunRequest(BaseModel):
    plan_id: str
    email_ids: list[str] = Field(min_length=1, max_length=20)
    max_workers: int = Field(default=4, ge=1, le=8)


class RunDecision(BaseModel):
    approved_by: str = Field(min_length=3, max_length=200)


class DraftEdit(BaseModel):
    body: str = Field(min_length=1, max_length=20000)


class DraftCreate(BaseModel):
    email_id: str
    body: str = Field(min_length=1, max_length=20000)
    confidence: float = Field(default=0.5, ge=0, le=1)
    source_template: str | None = None


class DraftDecision(BaseModel):
    approved_by: str = Field(min_length=3, max_length=200)


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    email_ids: list[str] | None = Field(default=None, max_length=20)


class OperationsRequest(BaseModel):
    incident: str = Field(min_length=3, max_length=1000)


class SdlcRequest(BaseModel):
    requirement: str = Field(min_length=3, max_length=2000)


class GovernanceRequest(BaseModel):
    action: str = Field(min_length=3, max_length=500)
    risk_level: Literal["low", "medium", "high"]
    evidence: str = Field(min_length=3, max_length=2000)
    owner_approved: bool = False
    approved_by: str | None = Field(default=None, max_length=200)


class DomainRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class CapstoneRequest(BaseModel):
    objective: str = Field(min_length=3, max_length=1000)


class CapstoneDecision(BaseModel):
    approved_by: str = Field(min_length=3, max_length=200)


def clarify_request(request: str) -> list[str]:
    normalized = request.lower()
    questions = []
    if not any(word in normalized for word in ("inbox", "emails", "email")):
        questions.append("Should I focus on your full inbox or a specific set of emails?")
    if any(word in normalized for word in ("reply", "respond", "draft")):
        questions.append("I will prepare drafts only. Do you want every draft reviewed before any use?")
    else:
        questions.append("Should I include reply drafts for messages that need a response?")
    return questions


def build_plan(request: str) -> ExecutionPlan:
    planner = EmailOrganizerPlannerAgent()
    agent_plan = planner.run()
    plan_id = f"plan_{uuid4().hex[:10]}"
    planner_instances[plan_id] = planner
    return ExecutionPlan(
        id=plan_id,
        request=request,
        goal="Triage the faculty inbox and prepare items for owner review",
        clarification_questions=[
            f"Confirm {field.replace('_', ' ')}: {value}"
            for field, value in planner.goal.items()
        ],
        steps=agent_plan["steps"],
        requirements=PlannerRequirements(**planner.goal),
        categories=agent_plan["categories"],
        iteration_log=planner.log,
        approval_required=agent_plan["approval_required_before_send"],
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "labs": "1-14", "mode": "mock"}


@app.get("/api/labs/advanced")
def advanced_labs_overview() -> dict[str, object]:
    labs = [
        {"number": 9, "title": "Deep Research Agent", "mode": "evidence-grounded", "output": "Cited findings from mock inbox"},
        {"number": 10, "title": "Cloud Operations Agent", "mode": "simulation", "output": "Diagnostics and operator-reviewed recovery plan"},
        {"number": 11, "title": "Agentic SDLC Factory", "mode": "deterministic checks", "output": "Requirement, acceptance criteria, and test results"},
        {"number": 12, "title": "Safety & Governance", "mode": "policy evaluation", "output": "Decision, approval gate, audit record, and rollback plan"},
        {"number": 13, "title": "Discipline-Specific Agent", "mode": "CSE (AI)", "output": "Domain findings with mailbox evidence"},
        {"number": 14, "title": "Capstone Project Studio", "mode": "integrated workflow", "output": "Research + SDLC + governance, pending owner approval"},
    ]
    return {"labs": labs, "history": advanced_labs.history()}


@app.post("/api/labs/research")
def run_deep_research(payload: ResearchRequest) -> dict[str, object]:
    if payload.email_ids:
        unknown = [email_id for email_id in payload.email_ids if connector.read_email(email_id) is None]
        if unknown:
            raise HTTPException(status_code=404, detail=f"Unknown email IDs: {', '.join(unknown)}")
    return advanced_labs.research(payload.question.strip(), payload.email_ids)


@app.post("/api/labs/operations/diagnose")
def diagnose_cloud_operations(payload: OperationsRequest) -> dict[str, object]:
    return advanced_labs.diagnose_operations(payload.incident.strip())


@app.post("/api/labs/sdlc/run")
def run_agentic_sdlc(payload: SdlcRequest) -> dict[str, object]:
    return advanced_labs.run_sdlc(payload.requirement.strip())


@app.post("/api/labs/governance/evaluate")
def evaluate_safety_governance(payload: GovernanceRequest) -> dict[str, object]:
    return advanced_labs.evaluate_governance(
        payload.action.strip(),
        payload.risk_level,
        payload.evidence.strip(),
        payload.owner_approved,
        payload.approved_by,
    )


@app.post("/api/labs/domain/run")
def run_domain_agent(payload: DomainRequest) -> dict[str, object]:
    return advanced_labs.analyze_domain(payload.question.strip())


@app.post("/api/labs/capstone/run")
def run_capstone(payload: CapstoneRequest) -> dict[str, object]:
    return advanced_labs.run_capstone(payload.objective.strip())


@app.post("/api/labs/capstone/{record_id}/approve")
def approve_capstone(record_id: str, decision: CapstoneDecision) -> dict[str, object]:
    try:
        return advanced_labs.decide_capstone(record_id, decision.approved_by.strip(), approve=True)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/labs/capstone/{record_id}/reject")
def reject_capstone(record_id: str, decision: CapstoneDecision) -> dict[str, object]:
    try:
        return advanced_labs.decide_capstone(record_id, decision.approved_by.strip(), approve=False)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/api/emails")
def read_emails(query: str | None = None) -> list[dict[str, object]]:
    return connector.search_emails(query) if query else connector.read_inbox()


@app.get("/api/emails/{email_id}")
def read_email(email_id: str) -> dict[str, object]:
    email = connector.read_email(email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@app.get("/api/emails/{email_id}/analysis")
def read_email_analysis(email_id: str) -> dict[str, object]:
    email_data = connector.read_email(email_id)
    if email_data is None:
        raise HTTPException(status_code=404, detail="Email not found")
    for run_results in reversed(list(agent_graph.results.values())):
        for result in run_results:
            if result.email_id == email_id:
                return result.model_dump()
    email = EmailMessage.model_validate(email_data)
    contacts = [Contact.model_validate(item) for item in connector.read_contacts()]
    replies = [PriorReply.model_validate(item) for item in connector.read_previous_replies(email.sender)]
    events = [CalendarEvent.model_validate(item) for item in connector.read_calendar()]
    return {
        "email_id": email_id,
        "classification": classify_email(email, contacts).model_dump(),
        "priority": calculate_priority(email).model_dump(),
        "draft_reply": draft_reply(email, replies).model_dump(),
        "action_items": [item.model_dump() for item in extract_action_items(email)],
        "follow_up": prepare_follow_up(email).model_dump(),
        "calendar_suggestion": prepare_calendar_suggestion(email, events).model_dump(),
        "approval_status": "pending",
        "archived": False,
    }


@app.get("/api/contacts")
def read_contacts() -> list[dict[str, object]]:
    return connector.read_contacts()


@app.get("/api/audit-logs")
def read_audit_logs() -> list[dict[str, object]]:
    return sorted(connector.read_audit_logs(), key=lambda entry: entry.get("timestamp", ""), reverse=True)


@app.get("/api/drafts")
def read_drafts() -> list[dict[str, object]]:
    return connector.read_drafts()


@app.post("/api/drafts")
def create_draft(payload: DraftCreate) -> dict[str, object]:
    try:
        draft = connector.save_draft(
            payload.email_id,
            payload.body,
            confidence=payload.confidence,
            source_template=payload.source_template,
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    connector.save_audit_log({"agent": "Human Review", "action": "save_draft", "status": "success", "email_id": payload.email_id, "draft_id": draft["id"]})
    return draft


@app.put("/api/drafts/{draft_id}")
def edit_draft(draft_id: str, payload: DraftEdit) -> dict[str, object]:
    try:
        return connector.update_draft(draft_id, body=payload.body)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/drafts/{draft_id}/approve")
def approve_draft(draft_id: str, decision: DraftDecision) -> dict[str, object]:
    try:
        draft = connector.update_draft(draft_id, status="approved", approved_by=decision.approved_by)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    connector.save_audit_log({"agent": "Human Review", "action": "approve_draft", "status": "approved", "email_id": draft["email_id"], "draft_id": draft_id, "approved_by": decision.approved_by})
    return draft


@app.post("/api/drafts/{draft_id}/reject")
def reject_draft(draft_id: str, decision: DraftDecision) -> dict[str, object]:
    try:
        draft = connector.update_draft(draft_id, status="rejected", rejected_by=decision.approved_by)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    connector.save_audit_log({"agent": "Human Review", "action": "reject_draft", "status": "rejected", "email_id": draft["email_id"], "draft_id": draft_id, "rejected_by": decision.approved_by})
    return draft


@app.post("/api/drafts/{draft_id}/regenerate")
def regenerate_draft(draft_id: str) -> dict[str, object]:
    existing = connector.read_draft(draft_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    if existing["status"] != "draft":
        raise HTTPException(status_code=409, detail="Only unreviewed drafts can be regenerated")
    email = EmailMessage.model_validate(connector.read_email(existing["email_id"]))
    replies = [PriorReply.model_validate(item) for item in connector.read_previous_replies(email.sender)]
    generated = draft_reply(email, replies)
    try:
        return connector.update_draft(draft_id, body=generated.body, confidence=generated.confidence, source_template=generated.source_template)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/api/action-items")
def read_action_items() -> list[dict[str, object]]:
    items = [task for task in connector.read_tasks()]
    for run_id, results in agent_graph.results.items():
        for result in results:
            items.extend({**item.model_dump(), "id": f"{run_id}:{result.email_id}:{index}", "email_id": result.email_id} for index, item in enumerate(result.action_items))
    return items


@app.get("/api/follow-ups")
def read_follow_ups() -> list[dict[str, object]]:
    return [
        {"email_id": result.email_id, **result.follow_up.model_dump()}
        for results in agent_graph.results.values()
        for result in results
        if result.follow_up.recommended
    ]


@app.get("/api/calendar/suggestions")
def read_calendar_suggestions() -> list[dict[str, object]]:
    return [
        {"email_id": result.email_id, **result.calendar_suggestion.model_dump()}
        for results in agent_graph.results.values()
        for result in results
        if result.calendar_suggestion.meeting_detected
    ]


@app.get("/api/dashboard/stats")
def dashboard_stats() -> dict[str, object]:
    emails = connector.read_inbox()
    priorities = {priority: sum(email["priority"] == priority for email in emails) for priority in ("URGENT", "HIGH", "MEDIUM", "LOW")}
    categories: dict[str, int] = {}
    for email in emails:
        category = email["sender_category"]
        categories[category] = categories.get(category, 0) + 1
    all_results = [result for results in agent_graph.results.values() for result in results]
    drafts = connector.read_drafts()
    return {
        "total_emails": len(emails),
        "unread": sum(not email["read"] for email in emails),
        "high_priority": priorities["URGENT"] + priorities["HIGH"],
        "pending_replies": sum(email["requires_reply"] for email in emails),
        "action_items": len(connector.read_tasks()) + sum(len(result.action_items) for result in all_results),
        "follow_ups": sum(result.follow_up.recommended for result in all_results),
        "pending_approvals": sum(draft["status"] == "draft" for draft in drafts),
        "priority_distribution": priorities,
        "category_distribution": categories,
    }


@app.post("/api/agent/run")
async def run_agent(payload: AgentRunRequest) -> dict[str, object]:
    plan = plans.get(payload.plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status != "locked":
        raise HTTPException(status_code=409, detail="Lock the plan before execution")
    unknown_ids = [email_id for email_id in payload.email_ids if connector.read_email(email_id) is None]
    if unknown_ids:
        raise HTTPException(status_code=404, detail=f"Unknown email IDs: {', '.join(unknown_ids)}")
    run, results, merge = await agent_graph.run_parallel(plan, payload.email_ids, payload.max_workers)
    return {"run": run.model_dump(), "results": [result.model_dump() for result in results], "merge": merge}


@app.get("/api/agent/runs")
def list_agent_runs() -> list[dict[str, object]]:
    return [run.model_dump() for run in agent_graph.runtime.list_runs()]


@app.get("/api/agent/runs/{run_id}")
def get_agent_run(run_id: str) -> dict[str, object]:
    try:
        run = agent_graph.runtime.get_run(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {
        "run": run.model_dump(),
        "results": [result.model_dump() for result in agent_graph.results.get(run_id, [])],
        "merge": agent_graph.merges.get(run_id),
    }


@app.post("/api/agent/runs/{run_id}/approve")
def approve_agent_run(run_id: str, decision: RunDecision) -> dict[str, object]:
    try:
        results = agent_graph.approve_run(run_id, decision.approved_by)
        run = agent_graph.runtime.get_run(run_id)
    except (KeyError, ValueError, PermissionError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"run": run.model_dump(), "results": [result.model_dump() for result in results]}


@app.post("/api/agent/runs/{run_id}/reject")
def reject_agent_run(run_id: str, decision: RunDecision) -> dict[str, object]:
    try:
        results = agent_graph.reject_run(run_id, decision.approved_by)
        run = agent_graph.runtime.get_run(run_id)
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"run": run.model_dump(), "results": [result.model_dump() for result in results]}


@app.post("/api/agent/plan", response_model=ExecutionPlan)
def create_plan(payload: PlanRequest) -> ExecutionPlan:
    plan = build_plan(payload.request.strip())
    plans[plan.id] = plan
    return plan


@app.put("/api/agent/plan/{plan_id}", response_model=ExecutionPlan)
def revise_plan(plan_id: str, payload: PlanRevision) -> ExecutionPlan:
    plan = plans.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status == "locked":
        raise HTTPException(status_code=409, detail="Locked plans cannot be revised")
    plan.goal = payload.goal.strip()
    plan.steps = [step.strip() for step in payload.steps if step.strip()]
    if not plan.steps:
        raise HTTPException(status_code=422, detail="A plan must contain at least one step")
    if payload.merge_vendor_into_other:
        planner = planner_instances[plan_id]
        revised = planner.revise({"merge_categories": {"vendor": "other"}})
        plan.categories = revised["categories"]
        plan.iteration_log = planner.log
    plans[plan_id] = plan
    return plan


@app.post("/api/agent/plan/{plan_id}/lock", response_model=ExecutionPlan)
def lock_plan(plan_id: str) -> ExecutionPlan:
    plan = plans.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.status = "locked"
    plans[plan_id] = plan
    return plan
