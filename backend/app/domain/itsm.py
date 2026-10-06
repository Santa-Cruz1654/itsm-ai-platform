from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TicketType


class ITSMRecord(BaseModel):
    """
    Normalized representation of a record created in an external ITSM
    platform.

    This model deliberately does not expose ServiceNow-specific concepts
    to the application layer.

    The application knows:

        external_system
        external_id
        external_number
        ticket_type
        status

    It does NOT need to know how ServiceNow stores those values.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    external_system: str = Field(
        min_length=1,
    )

    external_id: str = Field(
        min_length=1,
    )

    external_number: str = Field(
        min_length=1,
    )

    ticket_type: TicketType

    status: str = Field(
        min_length=1,
    )

    created_at: datetime

    updated_at: datetime