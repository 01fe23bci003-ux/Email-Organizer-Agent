import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.ai.provider import AIProvider, get_provider
from app.models.email import CalendarEvent, Contact, EmailMessage, PriorReply


class TriagePlanInput(BaseModel):
    mailbox_scope: str
    priority_categories: list[str]
    date_range: str
    standard_response_library_available: bool
    existing_folders: list[str] = Field(default_factory=list)
    feedback: dict[str, str] = Field(default_factory=dict)


class TriagePlanOutput(BaseModel):
    mailbox_scope: str
    date_range: str
    priority_categories: list[str]
    categories: list[str]
    standard_response_library_available: bool
    steps: list[str]
    approval_required_before_send: bool = True
    revision_applied: bool = False


class EmailClassification(BaseModel):
    sender_category: str
    content_type: str
    tags: list[str]
    confidence: float = Field(ge=0, le=1)
    sender_verified: bool


class PriorityAnalysis(BaseModel):
    priority: Literal["LOW", "MEDIUM", "HIGH", "URGENT"]
    urgency_score: int = Field(ge=0, le=100)
    reason: str
    detected_deadline: str | None = None
    requires_human_review: bool = False


class DraftReply(BaseModel):
    body: str
    source_template: str | None = None
    confidence: float = Field(ge=0, le=1)
    explanation: str
    prior_reply_used: bool
    status: Literal["draft"] = "draft"


class ExtractedActionItem(BaseModel):
    task: str
    deadline: str | None = None
    owner: str
    status: Literal["pending"] = "pending"


class FollowUpSuggestion(BaseModel):
    recommended: bool
    reason: str
    remind_on: str | None = None


class CalendarSuggestion(BaseModel):
    meeting_detected: bool
    proposed_time: str | None = None
    participants: list[str]
    available: bool | None = None
    recommendation: str
    requires_confirmation: bool = True


def plan_triage_skill(inputs: TriagePlanInput) -> TriagePlanOutput:
    categories = ["Student", "Faculty", "Administration", "Collaborator", "Vendor", "Other"]
    revision_applied = False
    if inputs.feedback.get("merge_vendor_into") == "other":
        categories.remove("Vendor")
        revision_applied = True
    return TriagePlanOutput(
        mailbox_scope=inputs.mailbox_scope,
        date_range=inputs.date_range,
        priority_categories=inputs.priority_categories,
        categories=categories,
        standard_response_library_available=inputs.standard_response_library_available,
        steps=[
            "Verify sender against contacts and read relevant thread history",
            "Classify, prioritize, and extract any requested actions",
            "Prepare a draft using approved prior replies when available",
            "Queue all consequential actions for mailbox-owner approval",
        ],
        revision_applied=revision_applied,
    )


def classify_email(email: EmailMessage, contacts: list[Contact]) -> EmailClassification:
    matched = next((contact for contact in contacts if contact.email.casefold() == email.sender.casefold()), None)
    verified = matched is not None and matched.category.casefold() == email.sender_category.casefold()
    text = f"{email.subject} {email.body}".casefold()
    tags = list(dict.fromkeys(email.tags + [word for word in ("deadline", "meeting", "assignment", "research", "follow-up") if word in text]))
    return EmailClassification(
        sender_category=matched.category if verified and matched else "Other",
        content_type=email.content_type,
        tags=tags,
        confidence=0.96 if verified else 0.42,
        sender_verified=verified,
    )


def calculate_priority(email: EmailMessage) -> PriorityAnalysis:
    text = f"{email.subject} {email.body}".casefold()
    detected_deadline = None
    date_match = re.search(r"\b(\d{1,2} \w+|\d{1,2}:\d{2} ?(?:am|pm)|today|tomorrow|by friday)\b", text)
    if date_match:
        detected_deadline = date_match.group(1)
    scores = {"LOW": 15, "MEDIUM": 40, "HIGH": 70, "URGENT": 92}
    priority = email.priority.upper()
    urgent_signal = any(signal in text for signal in ("urgent", "immediately", "by 4:00 pm", "action required"))
    if urgent_signal and priority in {"LOW", "MEDIUM"}:
        priority = "HIGH"
    confidence = 0.89 if priority in scores else 0.35
    return PriorityAnalysis(
        priority=priority if priority in scores else "MEDIUM",
        urgency_score=scores.get(priority, 40),
        reason="Explicit deadline or escalation language detected" if urgent_signal else f"Priority follows the email's current {email.priority} marker",
        detected_deadline=detected_deadline,
        requires_human_review=confidence < 0.5,
    )


def draft_reply(
    email: EmailMessage, context: list[PriorReply], provider: AIProvider | None = None
) -> DraftReply:
    prior = next((reply for reply in reversed(context) if reply.contact_email.casefold() == email.sender.casefold()), None)
    greeting_name = email.sender.split("@")[0].replace(".", " ").title()
    if prior:
        fallback = f"Dear {greeting_name},\n\nThank you for following up. {prior.body}\n\nBest regards,\nFaculty Team"
        source_template = "prior-contact-reply"
        explanation = "Adapted a stored reply from this sender's history; review names, dates, and details."
        confidence = 0.78
    else:
        fallback = f"Dear {greeting_name},\n\nThank you for your message about {email.subject}. I have received it and will review the details before responding further.\n\nBest regards,\nFaculty Team"
        source_template = None
        explanation = "Created a neutral acknowledgement because no matching prior reply was found."
        confidence = 0.62
    selected_provider = provider or get_provider()
    body = selected_provider.complete(
        "draft_reply",
        {
            "sender": email.sender,
            "subject": email.subject,
            "email_body": email.body,
            "previous_reply": prior.body if prior else None,
            "fallback_draft": fallback,
            "must_not_send": True,
        },
    )
    return DraftReply(
        body=body,
        source_template=source_template,
        confidence=confidence,
        explanation=f"{explanation} Provider: {selected_provider.name}.",
        prior_reply_used=prior is not None,
    )


def extract_action_items(email: EmailMessage) -> list[ExtractedActionItem]:
    text = f"{email.subject} {email.body}"
    actionable = any(term in text.casefold() for term in ("please", "submit", "upload", "confirm", "review", "nominate", "could you", "please let me know"))
    if not actionable:
        return []
    date_match = re.search(r"\b(\d{1,2} \w+|\d{1,2}:\d{2} ?(?:am|pm)|today|tomorrow|by friday|by monday)\b", text, re.IGNORECASE)
    owner = "student" if email.sender_category.casefold() == "student" else "mailbox_owner"
    return [ExtractedActionItem(task=email.subject, deadline=date_match.group(1) if date_match else None, owner=owner)]


def prepare_follow_up(email: EmailMessage) -> FollowUpSuggestion:
    followup_thread = email.content_type.casefold() == "follow-up" or "following up" in email.body.casefold()
    recommended = followup_thread or email.requires_reply
    reason = "Sender explicitly followed up; prioritize an owner reminder" if followup_thread else "Reply is requested; remind the owner if it remains unanswered" if recommended else "No reply or reminder signal detected"
    return FollowUpSuggestion(recommended=recommended, reason=reason)


def prepare_calendar_suggestion(email: EmailMessage, events: list[CalendarEvent]) -> CalendarSuggestion:
    text = f"{email.subject} {email.body}".casefold()
    meeting = email.content_type.casefold() == "meeting" or any(term in text for term in ("meet", "meeting", "call"))
    proposed = next((value for value in ("Thursday afternoon", "Tuesday at 11 AM", "Wednesday at 3 PM", "2:30 PM") if value.casefold() in text), None)
    return CalendarSuggestion(
        meeting_detected=meeting,
        proposed_time=proposed,
        participants=[email.sender, *email.recipients] if meeting else [],
        available=None if proposed is None else not any(proposed.casefold() in event.starts_at.casefold() for event in events),
        recommendation="Offer a suggested slot for owner review; do not book automatically" if meeting else "No meeting action suggested",
    )


def format_email_result(result: dict[str, Any]) -> dict[str, Any]:
    def serialize(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return {key: serialize(item) for key, item in value.model_dump().items()}
        if isinstance(value, dict):
            return {key: serialize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [serialize(item) for item in value]
        return value

    return serialize(result)