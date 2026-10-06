from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TicketStatus, TicketType


class CreateTicketRequest(BaseModel):
    """HTTP request for creating an ITSM ticket."""

    model_config = ConfigDict(
        extra="forbid"
    )

    user_id: str = Field(
        min_length=1,
    )

    type: TicketType

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )


class TicketResponse(BaseModel):
    """HTTP representation of an ITSM ticket."""

    model_config = ConfigDict(
        from_attributes=True
    )

    ticket_id: str

    user_id: str

    type: TicketType

    status: TicketStatus

    title: str

    description: str

    category: str | None = None

    subcategory: str | None = None

    priority: str | None = None

    impact: str | None = None

    urgency: str | None = None

    assignment_group: str | None = None

    # ---------------------------------------------------------------
    # External ITSM correlation
    # ---------------------------------------------------------------

    external_system: str | None = None

    external_ticket_id: str | None = None

    external_ticket_number: str | None = None

    external_sync_status: str

    external_sync_error: str | None = None

    created_at: datetime

    updated_at: datetime

    resolved_at: datetime | None = None