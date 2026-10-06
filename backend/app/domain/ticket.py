from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import TicketStatus, TicketType


class Ticket(BaseModel):
    """
    Internal ITSM ticket representation.

    MongoDB persists this model.

    External ITSM identifiers are optional because a ticket can exist
    locally before external synchronization succeeds.
    """

    ticket_id: str

    user_id: str

    type: TicketType

    status: TicketStatus = TicketStatus.NEW

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

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

    external_sync_status: str = "pending"

    external_sync_error: str | None = None

    created_at: datetime

    updated_at: datetime

    resolved_at: datetime | None = None