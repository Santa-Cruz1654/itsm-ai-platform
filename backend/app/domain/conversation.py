from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import (
    ConversationStatus,
    MessageRole,
    ResolutionType,
)


class Message(BaseModel):
    message_id: str
    role: MessageRole
    content: str = Field(min_length=1)
    created_at: datetime


class Resolution(BaseModel):
    type: ResolutionType
    summary: str = Field(min_length=1)
    resolved_at: datetime


class Conversation(BaseModel):
    conversation_id: str
    user_id: str

    status: ConversationStatus = ConversationStatus.ACTIVE

    messages: list[Message] = Field(default_factory=list)

    resolution: Resolution | None = None

    created_at: datetime
    updated_at: datetime