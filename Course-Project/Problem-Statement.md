# Problem Statement

## Artifact

**Email Organizer Agent** is the Agentic AI course Chapter 3 worklet. It explores a human-governed workflow for triaging a faculty inbox. The current implementation is a mock-mode prototype; it does not connect to a live mailbox.

## Team

| Name | USN | Division |
|---|---|---|
| Aman Yaligar | 01fe23bci003 | `<Div>` |
| Mallanagouda P | 01fe24bci402 | `<Div>` |
| Vinay C | 01fe23bci017 | `<Div>` |
| Abhay H | 01fe23bci014 | `<Div>` |

## Stakeholders

The primary stakeholder and decision-maker is the faculty member who owns the mailbox. Students, faculty colleagues, university administration, collaborators, and vendors are represented as correspondents in the seeded mock data.

## Problem Context

Faculty inboxes combine urgent administrative requests, student questions, meeting requests, follow-ups, and low-priority notices. Sorting messages, deciding what needs attention, and replying consistently takes time. Important deadlines can be buried; standard replies may be recreated instead of reused; meeting requests can be missed or double-booked; action items mentioned in passing may not be tracked; and follow-up reminders may be inconsistent.

The needs above are taken from the project brief. Stakeholder interview notes or other validation evidence: **TODO: add**.

## Proposed Solution

Build an agentic inbox assistant that classifies incoming messages, ranks priority and urgency, prepares review-only replies using stored prior replies where available, extracts candidate action items and meeting requests, suggests follow-ups, and presents its findings to the mailbox owner. Agents draft and flag; a named human approves. The system must never send a message or confirm a meeting without the faculty mailbox owner's approval.

The current prototype demonstrates this workflow against seeded mock email, contact, reply, calendar, and task data. It does not provide live mailbox access, external calendar synchronization, or email sending.

## Objectives

- Classify mock inbox messages and verify sender categories against the contact list.
- Assign priority signals and detect some deadline language.
- Prepare reply drafts that may reuse a stored prior reply, while leaving every draft in draft state.
- Extract candidate action items, follow-up reminders, and calendar suggestions.
- Validate structured results, record execution steps, and pause runs for mailbox-owner review.
- Keep an auditable record of draft and approval decisions.

## Target KPIs

These are acceptance targets, not measured results. **TODO: add measured results and evidence.**

| KPI | Target |
|---|---|
| Validation before owner review | 100% of validation checks pass before owner review. The current workflow records validation failures and routes the result to human review after bounded retries; it does not enforce this target. |
| Draft evidence | Every draft is grounded in thread history and past replies with an evidence record. The current mock draft may use a prior reply when available or a neutral fallback; a complete evidence record is not implemented. |
| Consequential actions | Zero consequential actions without approval. The prototype has no email-send or external calendar-write capability; approval identity is currently supplied by the caller and is not authenticated. |
| Audit and rollback | Full audit trail for every send and approval, with rollback. Approval events are logged; no send operation exists and rollback is not implemented. |

## Guardrails

- Never auto-send email. The current prototype has no send endpoint or send-capable connector.
- Never mark an extracted task complete without confirmation. Extracted action items are modeled as pending; there is no task-completion workflow.
- Never confirm or book a meeting without approval. The prototype provides suggestions only and performs no calendar writes.
- Audit every send and approval. Approval actions are logged; send auditing remains a future requirement if sending is ever added.
- Restrict access to the mailbox owner's own mailbox. **TODO: add authentication, authorization, and mailbox-scoped access controls before connecting a real mailbox.**
