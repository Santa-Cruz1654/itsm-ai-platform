from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import (
    AutomationStatus,
    ConsentSource,
    ExecutionStatus,
    PolicyDecision,
    ValidationStatus,
)


class Consent(BaseModel):
    granted: bool
    source: ConsentSource
    action: str = Field(min_length=1)
    timestamp: datetime


class PolicyResult(BaseModel):
    decision: PolicyDecision
    policy_id: str = Field(min_length=1)
    evaluated_at: datetime


class ExecutionResult(BaseModel):
    status: ExecutionStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class ValidationResult(BaseModel):
    status: ValidationStatus
    checks: list[str] = Field(default_factory=list)
    validated_at: datetime | None = None


class AutomationAction(BaseModel):
    action_id: str
    user_id: str

    ticket_id: str | None = None
    conversation_id: str | None = None

    action: str = Field(min_length=1)
    tool: str = Field(min_length=1)

    status: AutomationStatus = AutomationStatus.REQUESTED

    consent: Consent
    policy: PolicyResult
    execution: ExecutionResult
    validation: ValidationResult

    result: str | None = None

    created_at: datetime
    completed_at: datetime | None = None