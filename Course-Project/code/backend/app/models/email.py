from pydantic import BaseModel, Field


class EmailMessage(BaseModel):
    id: str
    thread_id: str
    sender: str
    recipients: list[str]
    subject: str
    body: str
    timestamp: str
    read: bool
    sender_category: str
    content_type: str
    priority: str
    tags: list[str] = Field(default_factory=list)
    requires_reply: bool = False


class Contact(BaseModel):
    email: str
    display_name: str
    category: str


class PriorReply(BaseModel):
    contact_email: str
    thread_id: str
    body: str
    created_at: str


class CalendarEvent(BaseModel):
    title: str
    starts_at: str
    ends_at: str
    participants: list[str]


class TaskRecord(BaseModel):
    id: str
    title: str
    deadline: str | None = None
    owner: str
    status: str = "pending"