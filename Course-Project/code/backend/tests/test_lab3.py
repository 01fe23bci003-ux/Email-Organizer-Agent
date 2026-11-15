from app.data.mock_data import MOCK_CALENDAR, MOCK_CONTACTS, MOCK_EMAILS, MOCK_PREVIOUS_REPLIES
from app.ai.provider import get_provider
from app.skills.email_skills import (
    TriagePlanInput,
    calculate_priority,
    classify_email,
    draft_reply,
    extract_action_items,
    format_email_result,
    plan_triage_skill,
    prepare_calendar_suggestion,
    prepare_follow_up,
)


def test_reusable_plan_skill_applies_feedback_and_keeps_approval_gate():
    plan = plan_triage_skill(
        TriagePlanInput(
            mailbox_scope="faculty_inbox",
            priority_categories=["URGENT", "HIGH"],
            date_range="all_unprocessed",
            standard_response_library_available=True,
            feedback={"merge_vendor_into": "other"},
        )
    )
    assert plan.revision_applied is True
    assert "Vendor" not in plan.categories
    assert plan.approval_required_before_send is True


def test_email_skills_return_typed_reviewable_outputs():
    email = MOCK_EMAILS[2]
    classification = classify_email(email, MOCK_CONTACTS)
    priority = calculate_priority(email)
    draft = draft_reply(email, MOCK_PREVIOUS_REPLIES)
    actions = extract_action_items(email)
    followup = prepare_follow_up(email)
    calendar = prepare_calendar_suggestion(MOCK_EMAILS[1], MOCK_CALENDAR)
    formatted = format_email_result({"classification": classification, "priority": priority, "draft": draft})

    assert classification.sender_verified is True
    assert priority.priority == "URGENT"
    assert draft.status == "draft"
    assert actions and actions[0].status == "pending"
    assert followup.recommended is True
    assert calendar.meeting_detected is True and calendar.requires_confirmation is True
    assert formatted["draft"]["status"] == "draft"
    assert get_provider().name == "mock"