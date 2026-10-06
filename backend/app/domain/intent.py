from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import ConfidenceLevel, IntentType


class AIIntentAnalysis(BaseModel):
    """
    Validated structured representation of an employee's ITSM intent.

    This model represents AI analysis only.

    It does not:
        - create or update tickets
        - execute automation
        - call external tools
        - call ServiceNow
        - perform knowledge retrieval
        - generate an employee-facing answer

    Downstream application services are responsible for making
    deterministic workflow decisions from this validated object.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    intent: IntentType

    category: str | None = None
    subcategory: str | None = None

    priority: str | None = None
    impact: str | None = None
    urgency: str | None = None

    assignment_group: str | None = None

    summary: str = Field(min_length=1)

    confidence: ConfidenceLevel

    automation_candidate: bool = False

    software_name: str | None = None

    @field_validator(
        "category",
        "subcategory",
        "priority",
        "impact",
        "urgency",
        "assignment_group",
        "software_name",
    )
    @classmethod
    def validate_optional_strings(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Optional strings may be omitted or null, but must not contain
        only whitespace.
        """
        if value is not None and not value:
            raise ValueError("value cannot be empty")

        return value

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        """
        Summary must contain meaningful text after whitespace stripping.
        """
        if not value:
            raise ValueError("summary cannot be empty")

        return value