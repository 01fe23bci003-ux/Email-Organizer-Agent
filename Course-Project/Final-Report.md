# Final Course Project Report

## Title Page

**Artifact:** Email Organizer Agent  
**Course:** Agentic AI, Chapter 3 worklet  
**Institution:** KLE Technological University, Hubballi  

| Name | USN | Division |
|---|---|---|
| Aman Yaligar | 01fe23bci003 | `<Div>` |
| Mallanagouda P | 01fe24bci402 | `<Div>` |
| Vinay C | 01fe23bci017 | `<Div>` |
| Abhay H | 01fe23bci014 | `<Div>` |

## Abstract

Email Organizer Agent is a mock-mode prototype that demonstrates a human-governed workflow for faculty inbox triage. A planning API creates and locks an execution plan; asynchronous workers then classify seeded messages, estimate urgency, prepare draft replies, extract candidate action items, and suggest follow-ups and calendar responses. Structured validation and an approval checkpoint keep results reviewable before an approved run can be archived. SQLite stores drafts and audit records. The React interface exposes inbox workspaces, run review, planning, and course-lab demonstrations. The system does not connect to a live mailbox, send email, or write to an external calendar. Backend tests and a frontend production build were run; measured operational KPIs are not available.

## Introduction

Faculty inboxes contain different kinds of work, including student questions, administrative deadlines, meeting requests, and notices. This project applies an agentic workflow to those needs while keeping consequential decisions with a human. The current implementation is deterministic and uses seeded mock records. Its purpose is to demonstrate orchestration, typed outputs, validation, review, and audit behavior rather than production email automation.

## Problem Statement

Important requests may be overlooked among low-priority messages. Replies can be inconsistent when common questions are answered from scratch. Meeting requests and implied action items can be missed, and follow-up reminders may not be tracked consistently. The proposed system classifies mail, ranks urgency, drafts replies, extracts action items and meeting requests, tracks follow-up suggestions, and requires a named faculty owner to review consequential outcomes. It must not send messages without approval.

The stakeholder needs documented here come from the project brief. Interview evidence: **TODO: add**. See [Problem-Statement.md](Problem-Statement.md) for the full statement and guardrails.

## Objectives

- Demonstrate a clarify, plan, revise, and lock workflow before inbox processing.
- Analyze mock emails with typed classification, priority, reply, action-item, follow-up, and calendar-suggestion outputs.
- Validate selected invariants and bound reprocessing to at most two retries.
- Pause completed runs for named human approval or rejection.
- Record run steps and approval events in an audit store.
- Provide a frontend for inbox triage, draft review, agent runs, audit records, planning, and Labs 1-14 demonstrations.

## System Architecture

The backend is a FastAPI application. The coordinator and API handlers in `app/main.py` create plans, enforce plan locking, start graph runs, and expose approval decisions. `EmailAgentGraph` in `app/graph/email_graph.py` processes messages with bounded parallel workers and combines results in request order. Per-email processing calls deterministic skills and validates structured results. `MockEmailConnector` is the mailbox boundary and reads seeded records; it stores drafts and audit records through `MemoryStore`. `AgentRuntime` tracks steps, checkpoints, retries, run status, and approval state.

```text
[Coordinator / Plan Review]
              |
              v
[Ingestion & Classification]
              |
              v
[Priority & Urgency]
              |
              v
[Draft Reply]
              |
              v
[Action-Item Extraction]
              |
              v
[Follow-up / Reminder Suggestion]
              |
              v
[Calendar & Task Suggestions (mock; no external sync)]
              |
              v
        [Validation] -- fail, retries remain (max 2) --> [Re-run classification]
              |                                            |
              +<-------------------------------------------+
              |
              | pass, or retry limit reached (issues retained)
              v
[Faculty Review (human gate)]
       | approved                    | rejected
       v                             v
[Archive & Audit Logging]          [End]
       |
       v
      [End]
```

A run remains in `waiting_for_approval` until an approval or rejection endpoint is called. Approval allows the application to mark results archived; it does not send an email. Validation retries rerun classification, not the complete downstream processing chain. `AgentRuntime` persists individual audit entries via the connector, while current plans, runs, and graph results are held in application memory.

## Agent Roster

| Agent or component | Role in the implemented prototype | Guardrail or boundary |
|---|---|---|
| Coordinator (`main.py`) | Builds, revises, and locks plans; validates requested email IDs; starts runs and exposes review endpoints. | The API rejects execution for an unlocked plan. There is no email-send endpoint. |
| `EmailOrganizerPlannerAgent` | Produces the deterministic Lab 1 clarify-plan workflow and records revisions. | Uses simulated answers and requires plan locking before execution. |
| `EmailAgentGraph` | Runs per-email stages, validates results, applies bounded retries, merges parallel workers, and queues results for human review. | Worker limit is bounded by the request model; drafts remain draft and action items remain pending. |
| Email skills | Classify against contacts, calculate priority, prepare a draft, extract candidate tasks, suggest follow-ups, and prepare calendar suggestions. | The mock AI provider returns a fallback draft; calendar output is a suggestion, not a booking. |
| `AdvancedLabsService` | Provides deterministic Labs 9-14 demonstrations for research, operations, SDLC, governance, domain analysis, and capstone. | Operations and mailbox evidence are simulated; governance evaluations do not execute external actions. |
| `EmailOrganizerToolAgent` | Runs registered inbox-reading and calculation helpers and records tool traces. | Tools expose mock data operations; they do not send email or alter a live mailbox. |
| `AgentRuntime` | Tracks runs, steps, checkpoints, retries, review state, and audit actions. | Requires review state before approval and approved state before archive authorization. |
| Human reviewer | Approves or rejects drafts, agent runs, and capstone records through API actions. | The approver name is caller-provided; identity authentication and authorization are not implemented. |

## Data Model

Pydantic models in `app/models/email.py` describe `EmailMessage`, `Contact`, `PriorReply`, `CalendarEvent`, and `TaskRecord`. The skills module defines typed classification, priority, draft, extracted action-item, follow-up, calendar-suggestion, and triage-plan inputs/outputs. The graph defines per-email results and validation results. Runtime models represent runs and individual steps, including state, timing, checkpoint data, and reviewer identity.

`MemoryStore` creates SQLite tables for contacts, prior replies, email history, drafts, and audit logs. The connector seeds contacts, previous replies, and email history from mock data when the store is empty. Run state and plan state are in process memory; they are not durable across backend restarts.

## Implementation Details

### Backend

The backend uses Python, FastAPI, Pydantic, SQLite, and a provider interface. The default `MockAIProvider` needs no API key and returns the deterministic fallback reply. `backend/.env.example` selects `AI_PROVIDER=mock`. A provider factory can be registered in code, but no production provider is configured in this repository.

The `app` package is organized as follows:

| Path | Responsibility |
|---|---|
| `app/main.py` | FastAPI app, request models, health route, planning, email, draft, run, review, dashboard, and Labs endpoints. |
| `app/agents/` | Lab 1 planner and deterministic Labs 9-14 service. |
| `app/ai/` | `AIProvider` protocol, mock provider, and provider registry. |
| `app/connectors/` | Mock mailbox connector, data access, draft updates, and persistence boundary. |
| `app/data/` | Seeded mock emails, contacts, prior replies, calendar events, and tasks. |
| `app/graph/` | Email processing graph, validation, bounded classification retries, worker fan-out, and result merge. |
| `app/memory/` | In-memory run state and SQLite-backed contact, reply, draft, email-history, and audit storage. |
| `app/models/` | Pydantic email-domain models. |
| `app/runtime/` | Run/step state transitions, checkpoints, approval, rejection, archive authorization, and audit calls. |
| `app/skills/` | Planning, classification, priority, reply drafting, action extraction, follow-up, and calendar suggestion logic. |
| `app/tools/` | Registered mock inbox tools, verified priority report, and calculation helper. |
| `backend/tests/` | API workflow and Lab 1-14 tests. |

The API includes health and mock inbox routes; contact, analysis, draft, action-item, follow-up, calendar-suggestion, dashboard, and audit routes; plan create/revise/lock routes; run start/list/detail/approve/reject routes; and Lab 9-14 research, operations, SDLC, governance, domain, and capstone routes. FastAPI's generated API reference is available at `/docs` when the service is running.

### Frontend

The frontend uses React 18, TypeScript, Vite, Tailwind's Vite plugin, and Lucide icons. `src/App.tsx` provides navigation, the Lab 1 plan-review experience, and the shell for workspace views and the advanced-labs view. `WorkspaceView.tsx` and `AdvancedLabsView.tsx` contain the corresponding workspace and Lab 9-14 interfaces. The Vite development server proxies `/api` requests to `http://127.0.0.1:8000`.

### API Endpoints

The implemented endpoint groups include:

- `GET /api/health`, `GET /api/labs/advanced`
- `GET /api/emails`, `GET /api/emails/{email_id}`, `GET /api/emails/{email_id}/analysis`
- `GET /api/contacts`, `GET /api/audit-logs`, `GET /api/drafts`, `POST /api/drafts`
- `PUT /api/drafts/{draft_id}`, `POST /api/drafts/{draft_id}/approve`, `/reject`, and `/regenerate`
- `GET /api/action-items`, `/api/follow-ups`, `/api/calendar/suggestions`, and `/api/dashboard/stats`
- `POST /api/agent/plan`, `PUT /api/agent/plan/{plan_id}`, `POST /api/agent/plan/{plan_id}/lock`
- `POST /api/agent/run`, `GET /api/agent/runs`, `GET /api/agent/runs/{run_id}`, and run `/approve` and `/reject` actions
- `POST /api/labs/research`, `/operations/diagnose`, `/sdlc/run`, `/governance/evaluate`, `/domain/run`, and `/capstone/run`; capstone records also have `/approve` and `/reject` actions

## Validation and Safety

Before processing, the API requires a locked plan and rejects unknown email IDs. The graph checks that the sender category is in the locked plan, the sender category is verified against contacts, the reply remains in draft status, and extracted action items remain pending. It can retry classification at most twice after the initial validation. A result with unresolved issues is still queued for human review, with the issues retained and human review required.

Runs pause at `waiting_for_approval`; approval and rejection are recorded in the audit store. Archive authorization requires a completed, approved run. Draft approval/rejection actions also write audit entries. The mock connector has no external send or calendar-write method. These are application-level controls, not mailbox identity security: there is no authentication or authorization layer, no live mailbox scope enforcement, and no implemented rollback operation. The governance lab records a rollback plan as demonstration data; it does not perform rollback.

## Testing and Results

The backend test suite was run with pytest: **23 passed**. It covers API workflow and Labs 1-14 behavior, including the locked-plan execution flow and human approval gate. The frontend production build completed successfully using the package build script (`tsc -b && vite build`). The npm installation reported two high-severity dependency advisories; dependency changes were not part of this project task.

These are test/build results only. No live mailbox, external calendar, production workload, KPI benchmark, or measured accuracy evaluation was run. KPI measurements and evaluation evidence: **TODO: add**.

## Screenshots

- **TODO: add** dashboard screenshot at `docs/screenshots/dashboard.png`.
- **TODO: add** inbox and email detail screenshots at `docs/screenshots/inbox.png` and `docs/screenshots/email-detail.png`.
- **TODO: add** agent plan and human-review screenshots at `docs/screenshots/agent-plan.png` and `docs/screenshots/agent-review.png`.

## Limitations

- All mailbox, contacts, replies, calendar events, and tasks are seeded mock data; there is no Gmail, Microsoft Graph, or other live connector.
- The default provider is deterministic and does not provide an LLM integration.
- Classification, deadline extraction, action-item extraction, and meeting detection use simple rules and are not an evaluated production model.
- Prior reply reuse is conditional; the fallback draft is a neutral acknowledgement. A comprehensive evidence/provenance record for every draft is not implemented.
- The calendar and follow-up features produce suggestions, not external synchronization or scheduled notifications.
- The API has no authentication, authorization, or mailbox-owner identity verification.
- Plans, active runs, and graph results are in memory. Persisted SQLite records do not make those orchestration objects durable.
- Validation retries only re-run classification; unresolved validation issues are passed to human review rather than blocked from the queue.
- Rollback is described in the governance demonstration but is not an implemented state-restoration feature.

## Future Work

- Add a secure, owner-authorized mailbox connector and enforce mailbox-scoped access.
- Add authenticated human identities, authorization checks, and auditable approval identity.
- Introduce evidence records that link each draft claim and recommendation to the relevant thread or prior reply.
- Expand validation and decide whether unresolved validation failures should block review or require explicit exception handling.
- Add real task/calendar integration only behind explicit human approval, with idempotency and recovery controls.
- Add durable orchestration state, operational monitoring, and tested rollback for supported external actions.
- Evaluate classification, urgency, draft grounding, and action extraction against a reviewed dataset; report measured KPI results.
- Capture application screenshots and validate the interface across target devices.

## Conclusion

The project implements a working mock inbox workflow that demonstrates planning, parallel processing, typed results, validation, human review, audit logging, and a React interface. The backend tests and frontend build provide reproducible software checks, but they do not establish production readiness or the target KPIs. Live mailbox access, authenticated approval, external synchronization, rollback, and measured evaluation remain future work.

## References

1. Project source: `Course-Project/code/backend/app/` and `Course-Project/code/frontend/src/`.
2. FastAPI documentation: https://fastapi.tiangolo.com/
3. Pydantic documentation: https://docs.pydantic.dev/
4. React documentation: https://react.dev/learn
5. TypeScript documentation: https://www.typescriptlang.org/docs/
6. Vite documentation: https://vite.dev/guide/
7. SQLite documentation: https://www.sqlite.org/docs.html
