from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import (
    get_intent_workflow_service,
)
from app.application.intent.intent_workflow_service import (
    IntentWorkflowResult,
)
from app.domain.enums import (
    ConfidenceLevel,
    ConsentSource,
    IntentType,
)


router = APIRouter(
    prefix="/intent",
    tags=["Intent"],
)


# ----------------------------------------------------------------------
# Request schema
# ----------------------------------------------------------------------


class IntentWorkflowRequest(BaseModel):
    """
    HTTP request for the AI-assisted ITSM workflow.

    The API accepts the employee's natural-language request together
    with the identity and optional consent information required by
    downstream workflows.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    employee_request: str = Field(
        min_length=1,
    )

    user_id: str | None = Field(
        default=None,
        min_length=1,
    )

    consent_granted: bool = False

    consent_source: ConsentSource = (
        ConsentSource.NOT_REQUIRED
    )

    create_escalation_ticket: bool = False


# ----------------------------------------------------------------------
# Response schemas
# ----------------------------------------------------------------------


class IntentAnalysisResponse(BaseModel):
    """
    HTTP representation of the validated AI intent analysis.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    intent: IntentType

    category: str | None = None

    subcategory: str | None = None

    priority: str | None = None

    impact: str | None = None

    urgency: str | None = None

    assignment_group: str | None = None

    summary: str

    confidence: ConfidenceLevel

    automation_candidate: bool

    software_name: str | None = None


class IntentRoutingDecisionResponse(BaseModel):
    """
    HTTP representation of the deterministic routing decision.
    """

    route: str

    reason: str

    requires_confirmation: bool

    requires_human_escalation: bool


class IntentWorkflowResponse(BaseModel):
    """
    HTTP representation of the complete AI-assisted ITSM workflow.
    """

    analysis: IntentAnalysisResponse

    decision: IntentRoutingDecisionResponse

    response: Any


# ----------------------------------------------------------------------
# Mapping helpers
# ----------------------------------------------------------------------


def _to_analysis_response(
    result: IntentWorkflowResult,
) -> IntentAnalysisResponse:
    """
    Convert the domain/application intent analysis into an
    HTTP response model.
    """

    analysis = result.analysis

    return IntentAnalysisResponse(
        intent=analysis.intent,
        category=analysis.category,
        subcategory=analysis.subcategory,
        priority=analysis.priority,
        impact=analysis.impact,
        urgency=analysis.urgency,
        assignment_group=analysis.assignment_group,
        summary=analysis.summary,
        confidence=analysis.confidence,
        automation_candidate=analysis.automation_candidate,
        software_name=analysis.software_name,
    )


def _to_routing_response(
    result: IntentWorkflowResult,
) -> IntentRoutingDecisionResponse:
    """
    Convert the deterministic application routing decision
    into an HTTP response model.
    """

    decision = result.decision

    return IntentRoutingDecisionResponse(
        route=decision.route,
        reason=decision.reason,
        requires_confirmation=(
            decision.requires_confirmation
        ),
        requires_human_escalation=(
            decision.requires_human_escalation
        ),
    )


def _to_workflow_response(
    result: IntentWorkflowResult,
) -> IntentWorkflowResponse:
    """
    Convert the complete application workflow result into
    the API response.
    """

    return IntentWorkflowResponse(
        analysis=_to_analysis_response(
            result
        ),
        decision=_to_routing_response(
            result
        ),
        response=result.response,
    )


# ----------------------------------------------------------------------
# Intent workflow endpoint
# ----------------------------------------------------------------------


@router.post(
    "",
    response_model=IntentWorkflowResponse,
    status_code=status.HTTP_200_OK,
)
async def process_intent(
    request: IntentWorkflowRequest,
    service=Depends(
        get_intent_workflow_service,
    ),
) -> IntentWorkflowResponse:
    """
    Process an employee request through the AI-assisted ITSM
    workflow.
    """

    result = service.handle(
        request.employee_request,
        user_id=request.user_id,
        consent_granted=request.consent_granted,
        consent_source=request.consent_source,
        create_escalation_ticket=(
            request.create_escalation_ticket
        ),
    )

    return _to_workflow_response(
        result
    )