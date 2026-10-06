from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AutomationStatus,
    ConsentSource,
)


class SelfHealingRequest(BaseModel):
    """
    Request to run the controlled self-healing workflow.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    user_id: str = Field(
        min_length=1
    )

    employee_request: str = Field(
        min_length=1
    )

    consent_granted: bool

    consent_source: ConsentSource


class SelfHealingResponse(BaseModel):
    """
    HTTP response for a self-healing workflow.
    """

    status: str
    message: str

    action_id: str | None = None
    action: str | None = None
    tool: str | None = None

    diagnosis: str | None = None

    knowledge_sources: list[
        dict[str, Any]
    ] | None = None

    automation_status: AutomationStatus | None = None

    validation_checks: list[str] | None = None

    ticket_id: str | None = None

    external_ticket_id: str | None = None

    external_ticket_number: str | None = None

    audit_event_ids: list[str] | None = None