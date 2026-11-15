# Email Organizer Agent

A mock-mode agentic workflow for triaging faculty email and preparing results for human review.

## Team Details

| Name | USN | Division |
|---|---|---|
| Aman Yaligar | 01fe23bci003 | `<B Div>` |
| Mallanagouda P | 01fe24bci402 | `<B Div>` |
| Vinay C | 01fe23bci017 | `<B Div>` |
| Abhay H | 01fe23bci014 | `<B Div>` |

## Quick Links

- [Assignments](./Assignments)
- [Course Project](./Course-Project)
- [Project code](./Course-Project/code)
- [Problem Statement](./Course-Project/Problem-Statement.md)
- [Final Report](./Course-Project/Final-Report.md)

## Assignments Overview

| No. | Title | Summary |
|---:|---|---|
| 1 | [To be added](./Assignments/Assignment-01) | To be added |
| 2 | To be added | To be added |
| 3 | To be added | To be added |
| 4 | To be added | To be added |
| 5 | To be added | To be added |
| 6 | To be added | To be added |
| 7 | To be added | To be added |
| 8 | To be added | To be added |
| 9 | To be added | To be added |
| 10 | To be added | To be added |
| 11 | To be added | To be added |
| 12 | To be added | To be added |

## Project

### Problem Statement

Faculty inboxes combine urgent administrative requests, student questions, meeting requests, follow-ups, and low-priority notices. Important requests can be buried; standard replies may be recreated; meetings and action items can be missed; and follow-ups may be inconsistent. This project demonstrates an agent that classifies and prioritizes mock inbox messages, drafts replies, and suggests actions for faculty review. Agents draft and flag; a named human approves. The current implementation uses seeded mock data and does not connect to a live mailbox.

### Objectives

- Classify mock messages and verify sender categories against contacts.
- Estimate priority and urgency, prepare draft-only replies, and extract candidate action items.
- Suggest follow-ups and possible calendar responses without making external changes.
- Validate structured results, record execution steps, and pause runs for human approval.
- Keep drafts and approval decisions auditable.

### Approach

```text
[Coordinator / plan review]
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
	 [Validation] -- fail; retries remain (max 2) --> [Re-run classification]
		 |                                               |
		 +<----------------------------------------------+
		 |
		 | pass, or retry limit reached (issues retained)
		 v
[Faculty Review (human gate)]
	| approved                     | rejected
	v                              v
[Archive & Audit Logging]          [End]
	|
	v
     [End]
```

Validation retries re-run classification, not the complete pipeline. A result with unresolved issues still reaches human review with its issues recorded. Approval authorizes archiving in the application; there is no email-send action.

### Implementation

**Technology:** Python, FastAPI, Pydantic, SQLite, React 18, TypeScript, Vite, Tailwind's Vite plugin, and Lucide icons. The default AI provider is a deterministic mock provider; no provider API key is required.

**Backend (`Course-Project/code/backend/app/`):**

- `main.py`: FastAPI endpoints for plans, inbox data, drafts, agent runs, review decisions, dashboard statistics, audit records, and Labs 9-14.
- `agents/`: clarify-plan workflow and deterministic advanced-lab demonstrations.
- `ai/`: provider interface, mock implementation, and provider registry.
- `connectors/`: mock mailbox access and persistence boundary; no live email or calendar adapter.
- `data/`: seeded mock emails, contacts, prior replies, calendar events, and tasks.
- `graph/`: per-email processing stages, validation, up to two retries, bounded parallel workers, and result merging.
- `memory/`: in-memory run state and SQLite storage for drafts and audit records, plus seeded contact, reply, and email history.
- `models/`: Pydantic email-domain models.
- `runtime/`: run and step state, checkpoints, approval/rejection, archive authorization, and audit calls.
- `skills/`: classification, priority, reply draft, action extraction, follow-up, and calendar-suggestion logic.
- `tools/`: registered mock inbox tools and calculation/verification helpers.
- `tests/`: backend API workflow and Labs 1-14 tests.

**Frontend (`Course-Project/code/frontend/`):** React and TypeScript workspace with dashboard, inbox, priority, action-item, draft, follow-up, calendar, agent-run, audit, planning, and Lab Studio views. Vite proxies `/api` requests to the backend at `http://127.0.0.1:8000`.

### Results

- Backend tests: **23 passed**.
- Frontend production build: **completed successfully**.
- Working behavior: plan review and locking, mock inbox analysis, draft generation, candidate task/follow-up/calendar suggestions, parallel agent runs, validation, human approval/rejection, archive status, and audit records.
- Screenshots: **TODO: add screenshots in docs/screenshots**.
- Limitations: no live mailbox, email sending, external calendar/task synchronization, authentication, mailbox-owner identity verification, durable run storage, or implemented rollback. Measured operational KPIs are **TODO: add**.
- Future work: secure mailbox integration, authenticated approvals, evidence records for drafts, durable orchestration, external actions behind approval, evaluation against reviewed data, and tested rollback.

## Repository Structure

```text
Email-Organizer-Agent/
├── README.md
├── .gitignore
├── Assignments/
│   ├── README.md
│   └── Assignment-01/README.md
└── Course-Project/
    ├── code/
    │   ├── backend/
    │   │   ├── app/
    │   │   ├── tests/
    │   │   ├── requirements.txt
    │   │   └── .env.example
    │   └── frontend/
    ├── Problem-Statement.md
    └── Final-Report.md
```

## How to Run

### Backend

In PowerShell, from the repository root:

```powershell
cd Course-Project\code\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The API documentation is at <http://127.0.0.1:8000/docs>. Run backend tests from the backend directory with `python -m pytest`.

### Frontend

In a second terminal, from the repository root:

```powershell
cd Course-Project\code\frontend
npm install
npm run dev
```

Vite prints the local frontend URL, normally <http://localhost:5173>.
