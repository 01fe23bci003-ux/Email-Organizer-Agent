import asyncio
from threading import Lock
from time import perf_counter
from typing import Any, Callable

from pydantic import BaseModel

from app.connectors.email_connector import EmailConnector, connector
from app.models.email import CalendarEvent, Contact, EmailMessage, PriorReply
from app.runtime.runtime import AgentRuntime, AgentRun
from app.skills.email_skills import (
    CalendarSuggestion,
    DraftReply,
    EmailClassification,
    ExtractedActionItem,
    FollowUpSuggestion,
    PriorityAnalysis,
    calculate_priority,
    classify_email,
    draft_reply,
    extract_action_items,
    prepare_calendar_suggestion,
    prepare_follow_up,
)


MAX_RETRIES = 2
NODE_GRAPH = {
    "START": ["INGESTION_CLASSIFICATION"],
    "INGESTION_CLASSIFICATION": ["PRIORITY_URGENCY"],
    "PRIORITY_URGENCY": ["DRAFT_REPLY"],
    "DRAFT_REPLY": ["ACTION_ITEM_EXTRACTION"],
    "ACTION_ITEM_EXTRACTION": ["FOLLOWUP_REMINDER"],
    "FOLLOWUP_REMINDER": ["CALENDAR_TASK_SYNC"],
    "CALENDAR_TASK_SYNC": ["VALIDATION"],
    "VALIDATION": ["INGESTION_CLASSIFICATION", "HUMAN_REVIEW"],
    "HUMAN_REVIEW": ["ARCHIVE_LOGGING", "END"],
    "ARCHIVE_LOGGING": ["END"],
    "END": [],
}


class NodeResult(BaseModel):
    node: str
    status: str
    duration_ms: float | None = None
    output_summary: str = ""


class ValidationResult(BaseModel):
    passed: bool
    issues: list[str]
    attempts: int
    requires_human_review: bool


class EmailProcessingResult(BaseModel):
    email_id: str
    draft_id: str
    classification: EmailClassification
    priority: PriorityAnalysis
    draft_reply: DraftReply
    action_items: list[ExtractedActionItem]
    follow_up: FollowUpSuggestion
    calendar_suggestion: CalendarSuggestion
    validation: ValidationResult
    nodes: list[NodeResult]
    approval_status: str = "pending"
    archived: bool = False


class EmailAgentGraph:
    def __init__(
        self,
        data_connector: EmailConnector = connector,
        runtime: AgentRuntime | None = None,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.connector = data_connector
        self.runtime = runtime or AgentRuntime(data_connector)
        self.max_retries = max_retries
        self.results: dict[str, list[EmailProcessingResult]] = {}
        self.merges: dict[str, dict[str, Any]] = {}
        self.active_workers = 0
        self.max_observed_workers = 0
        self.worker_lock = Lock()

    @staticmethod
    def _value(plan: Any, key: str, default: Any = None) -> Any:
        if isinstance(plan, BaseModel):
            plan = plan.model_dump()
        return plan.get(key, default)

    def _execute(
        self,
        run_id: str,
        email_id: str,
        node: str,
        summary: str,
        operation: Callable[[], Any],
    ) -> tuple[Any, NodeResult]:
        step_id = self.runtime.begin_step(run_id, node, summary, email_id)
        try:
            output = operation()
            output_summary = self._summarize(output)
            step = self.runtime.finish_step(run_id, step_id, output_summary)
            return output, NodeResult(node=node, status=step.status, duration_ms=step.duration_ms, output_summary=output_summary)
        except Exception as error:
            self.runtime.finish_step(run_id, step_id, "", str(error))
            raise

    @staticmethod
    def _summarize(output: Any) -> str:
        if isinstance(output, BaseModel):
            values = output.model_dump()
            return ", ".join(f"{key}={value}" for key, value in values.items() if key in {"priority", "sender_category", "content_type", "status", "meeting_detected"})
        if isinstance(output, list):
            return f"{len(output)} item(s)"
        return str(output)[:180]

    def validate_result(self, result: EmailProcessingResult, plan: Any) -> list[str]:
        issues = []
        categories = self._value(plan, "categories", [])
        allowed = {str(category).casefold() for category in categories}
        if result.classification.sender_category.casefold() not in allowed:
            issues.append("sender category is outside the locked plan categories")
        if not result.classification.sender_verified:
            issues.append("sender category could not be verified against contacts")
        if result.draft_reply.status != "draft":
            issues.append("reply output is not in draft-only state")
        if any(item.status != "pending" for item in result.action_items):
            issues.append("an action item was marked complete without owner review")
        return issues

    def process_email(self, run_id: str, email_id: str, plan: Any) -> EmailProcessingResult:
        raw_email = self.connector.read_email(email_id)
        if raw_email is None:
            raise KeyError(f"Email not found: {email_id}")
        email = EmailMessage.model_validate(raw_email)
        contacts = [Contact.model_validate(item) for item in self.connector.read_contacts()]
        nodes: list[NodeResult] = []
        classification, node = self._execute(
            run_id, email_id, "INGESTION_CLASSIFICATION", "Read email and verify sender category",
            lambda: classify_email(email, contacts),
        )
        nodes.append(node)

        categories = {str(item).casefold() for item in self._value(plan, "categories", [])}
        if classification.sender_category.casefold() not in categories and "other" in categories:
            classification.sender_category = "Other"
        priority, node = self._execute(
            run_id, email_id, "PRIORITY_URGENCY", "Calculate priority and detect deadline signals",
            lambda: calculate_priority(email),
        )
        nodes.append(node)

        previous = [PriorReply.model_validate(item) for item in self.connector.read_previous_replies(email.sender)]
        draft, node = self._execute(
            run_id, email_id, "DRAFT_REPLY", "Prepare review-only draft using thread history",
            lambda: draft_reply(email, previous),
        )
        nodes.append(node)
        saved = self.connector.save_draft(email_id, draft.body, confidence=draft.confidence, source_template=draft.source_template)
        draft_id = saved["id"]

        action_items, node = self._execute(
            run_id, email_id, "ACTION_ITEM_EXTRACTION", "Extract requested tasks and deadlines",
            lambda: extract_action_items(email),
        )
        nodes.append(node)
        follow_up, node = self._execute(
            run_id, email_id, "FOLLOWUP_REMINDER", "Suggest reminders for replies and follow-ups",
            lambda: prepare_follow_up(email),
        )
        nodes.append(node)
        calendar_events = [CalendarEvent.model_validate(item) for item in self.connector.read_calendar()]
        calendar_suggestion, node = self._execute(
            run_id, email_id, "CALENDAR_TASK_SYNC", "Check mock calendar and prepare suggestions",
            lambda: prepare_calendar_suggestion(email, calendar_events),
        )
        nodes.append(node)

        validation = ValidationResult(passed=False, issues=[], attempts=0, requires_human_review=False)
        for attempt in range(self.max_retries + 1):
            issues = self.validate_result(
                EmailProcessingResult(
                    email_id=email_id,
                    draft_id=draft_id,
                    classification=classification,
                    priority=priority,
                    draft_reply=draft,
                    action_items=action_items,
                    follow_up=follow_up,
                    calendar_suggestion=calendar_suggestion,
                    validation=validation,
                    nodes=nodes,
                ),
                plan,
            )
            validation = ValidationResult(
                passed=not issues,
                issues=issues,
                attempts=attempt + 1,
                requires_human_review=bool(issues) or priority.requires_human_review,
            )
            _, validation_node = self._execute(
                run_id,
                email_id,
                "VALIDATION",
                f"Validate structured result (attempt {attempt + 1})",
                lambda: validation,
            )
            nodes.append(validation_node)
            if not issues:
                break
            if attempt < self.max_retries:
                self.runtime.record_retry(run_id, "INGESTION_CLASSIFICATION", "; ".join(issues))
                classification, retry_node = self._execute(
                    run_id,
                    email_id,
                    "INGESTION_CLASSIFICATION",
                    f"Bounded reprocess after validation (retry {attempt + 1})",
                    lambda: classify_email(email, contacts),
                )
                nodes.append(retry_node)

        _, human_node = self._execute(
            run_id, email_id, "HUMAN_REVIEW", "Queue draft and findings for mailbox-owner decision",
            lambda: f"Waiting for owner review; draft={draft_id}",
        )
        nodes.append(human_node)
        return EmailProcessingResult(
            email_id=email_id,
            draft_id=draft_id,
            classification=classification,
            priority=priority,
            draft_reply=draft,
            action_items=action_items,
            follow_up=follow_up,
            calendar_suggestion=calendar_suggestion,
            validation=validation,
            nodes=nodes,
        )

    def run_serial(self, plan: Any, email_ids: list[str]) -> tuple[AgentRun, list[EmailProcessingResult]]:
        if self._value(plan, "status") != "locked":
            raise PermissionError("Execution requires an approved and locked plan")
        plan_id = self._value(plan, "id", "locked-plan")
        run = self.runtime.create_run(plan_id, email_ids)
        results = [self.process_email(run.id, email_id, plan) for email_id in email_ids]
        self.results[run.id] = results
        self.runtime.checkpoint(run.id, "HUMAN_REVIEW", {"processed_email_ids": email_ids})
        self.runtime.resume(run.id)
        self.runtime.wait_for_approval(run.id)
        return run, results

    def merge_results(
        self, plan: Any, email_ids: list[str], results: list[EmailProcessingResult]
    ) -> tuple[list[EmailProcessingResult], dict[str, Any]]:
        expected = set(email_ids)
        by_id: dict[str, EmailProcessingResult] = {}
        for result in results:
            if result.email_id not in expected:
                raise ValueError(f"Worker returned an email outside the locked batch: {result.email_id}")
            if result.email_id in by_id:
                raise ValueError(f"Duplicate worker result for email: {result.email_id}")
            by_id[result.email_id] = EmailProcessingResult.model_validate(result.model_dump())
        merged = [by_id[email_id] for email_id in email_ids if email_id in by_id]
        plan_categories = self._value(plan, "categories", [])
        requirements = self._value(plan, "requirements", {})
        priority_categories = requirements.get("priority_categories", []) if isinstance(requirements, dict) else []
        summary = {
            "plan_id": self._value(plan, "id"),
            "requested_email_ids": list(email_ids),
            "processed_count": len(merged),
            "failed_email_ids": [email_id for email_id in email_ids if email_id not in by_id],
            "plan_categories": plan_categories,
            "priority_categories": priority_categories,
            "priority_counts": {
                priority: sum(result.priority.priority == priority for result in merged)
                for priority in priority_categories
            },
            "category_counts": {
                category: sum(result.classification.sender_category.casefold() == str(category).casefold() for result in merged)
                for category in plan_categories
            },
            "merge_rule": "validated EmailProcessingResult keyed by email_id, emitted in locked request order",
        }
        return merged, summary

    def _run_worker(self, run_id: str, email_id: str, plan: Any) -> EmailProcessingResult:
        with self.worker_lock:
            self.active_workers += 1
            self.max_observed_workers = max(self.max_observed_workers, self.active_workers)
        try:
            return self.process_email(run_id, email_id, plan)
        finally:
            with self.worker_lock:
                self.active_workers -= 1

    async def run_parallel(
        self, plan: Any, email_ids: list[str], max_workers: int = 4
    ) -> tuple[AgentRun, list[EmailProcessingResult], dict[str, Any]]:
        if self._value(plan, "status") != "locked":
            raise PermissionError("Execution requires an approved and locked plan")
        if not email_ids:
            raise ValueError("At least one email must be selected")
        if len(email_ids) != len(set(email_ids)):
            raise ValueError("Email IDs must be unique within a batch")
        plan_id = self._value(plan, "id", "locked-plan")
        run = self.runtime.create_run(plan_id, email_ids)
        started = perf_counter()
        semaphore = asyncio.Semaphore(max(1, max_workers))

        async def process(email_id: str) -> EmailProcessingResult | Exception:
            async with semaphore:
                try:
                    return await asyncio.to_thread(self._run_worker, run.id, email_id, plan)
                except Exception as error:
                    self.connector.save_audit_log(
                        {"run_id": run.id, "agent": "Coordinator", "action": "worker_failure", "status": "failed", "email_id": email_id, "error": str(error)}
                    )
                    return error

        outcomes = await asyncio.gather(*(process(email_id) for email_id in email_ids))
        successful = [item for item in outcomes if isinstance(item, EmailProcessingResult)]
        merged, summary = self.merge_results(plan, email_ids, successful)
        summary.update(
            {
                "processing_mode": "parallel",
                "worker_limit": max(1, max_workers),
                "max_observed_workers": self.max_observed_workers,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            }
        )
        self.results[run.id] = merged
        self.merges[run.id] = summary
        self.runtime.checkpoint(run.id, "HUMAN_REVIEW", {"processed_email_ids": [item.email_id for item in merged], "failed_email_ids": summary["failed_email_ids"]})
        self.runtime.resume(run.id)
        self.runtime.wait_for_approval(run.id)
        self.connector.save_audit_log(
            {"run_id": run.id, "agent": "MergeSelector", "action": "fan_in_merge", "status": "success", "details": summary}
        )
        return run, merged, summary

    def approve_run(self, run_id: str, approved_by: str) -> list[EmailProcessingResult]:
        self.runtime.approve(run_id, approved_by)
        self.runtime.authorize_archive(run_id)
        for result in self.results.get(run_id, []):
            result.approval_status = "approved"
            result.archived = True
            self.connector.save_audit_log(
                {"run_id": run_id, "agent": "ArchiveAgent", "action": "archive_approved_result", "status": "success", "email_id": result.email_id, "approved_by": approved_by}
            )
        return self.results.get(run_id, [])

    def reject_run(self, run_id: str, rejected_by: str) -> list[EmailProcessingResult]:
        self.runtime.reject(run_id, rejected_by)
        for result in self.results.get(run_id, []):
            result.approval_status = "rejected"
        return self.results.get(run_id, [])