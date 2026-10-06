from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AutomationStatus,
    ConsentSource,
    ExecutionStatus,
    PolicyDecision,
    ValidationStatus,
)


class CreateAutomationRequest(BaseModel):
    """HTTP request model for creating an automation action."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    tool: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)

    policy_decision: PolicyDecision
    consent_granted: bool
    consent_source: ConsentSource

    ticket_id: str | None = None
    conversation_id: str | None = None


class ConsentResponse(BaseModel):
    granted: bool
    source: ConsentSource
    action: str
    timestamp: datetime


class PolicyResponse(BaseModel):
    decision: PolicyDecision
    policy_id: str
    evaluated_at: datetime


class ExecutionResponse(BaseModel):
    status: ExecutionStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class ValidationResponse(BaseModel):
    status: ValidationStatus
    checks: list[str]
    validated_at: datetime | None = None


class AutomationResponse(BaseModel):
    """HTTP response representation of an automation action."""

    model_config = ConfigDict(from_attributes=True)

    action_id: str
    user_id: str
    ticket_id: str | None
    conversation_id: str | None

    action: str
    tool: str
    status: AutomationStatus

    consent: ConsentResponse
    policy: PolicyResponse
    execution: ExecutionResponse
    validation: ValidationResponse

    result: str | None
    created_at: datetime
    completed_at: datetime | None