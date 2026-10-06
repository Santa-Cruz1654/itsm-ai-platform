from datetime import datetime

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    event_id: str
    event_type: str = Field(min_length=1)

    user_id: str

    conversation_id: str | None = None
    ticket_id: str | None = None
    action_id: str | None = None

    actor: str = Field(min_length=1)
    description: str = Field(min_length=1)

    metadata: dict[str, str] = Field(default_factory=dict)

    created_at: datetime