from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_automation_service
from app.api.schemas.automation import (
    AutomationResponse,
    ConsentResponse,
    CreateAutomationRequest,
    ExecutionResponse,
    PolicyResponse,
    ValidationResponse,
)
from app.application.automation_service import AutomationService
from app.domain.automation import AutomationAction


router = APIRouter(
    prefix="/automations",
    tags=["Automations"],
)


def _to_automation_response(
    action: AutomationAction,
) -> AutomationResponse:
    """
    Map the domain AutomationAction into the API response model.

    The API layer owns this translation so that domain models remain
    independent from HTTP/API concerns.
    """

    return AutomationResponse(
        action_id=action.action_id,
        user_id=action.user_id,
        ticket_id=action.ticket_id,
        conversation_id=action.conversation_id,
        action=action.action,
        tool=action.tool,
        status=action.status,
        consent=ConsentResponse(
            granted=action.consent.granted,
            source=action.consent.source,
            action=action.consent.action,
            timestamp=action.consent.timestamp,
        ),
        policy=PolicyResponse(
            decision=action.policy.decision,
            policy_id=action.policy.policy_id,
            evaluated_at=action.policy.evaluated_at,
        ),
        execution=ExecutionResponse(
            status=action.execution.status,
            started_at=action.execution.started_at,
            completed_at=action.execution.completed_at,
            error=action.execution.error,
        ),
        validation=ValidationResponse(
            status=action.validation.status,
            checks=action.validation.checks,
            validated_at=action.validation.validated_at,
        ),
        result=action.result,
        created_at=action.created_at,
        completed_at=action.completed_at,
    )


@router.post(
    "",
    response_model=AutomationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_automation(
    request: CreateAutomationRequest,
    service: AutomationService = Depends(get_automation_service),
) -> AutomationResponse:
    """
    Create an automation action after collecting the required
    policy and consent information.
    """

    action = service.create_action(
        user_id=request.user_id,
        action=request.action,
        tool=request.tool,
        policy_id=request.policy_id,
        policy_decision=request.policy_decision,
        consent_granted=request.consent_granted,
        consent_source=request.consent_source,
        ticket_id=request.ticket_id,
        conversation_id=request.conversation_id,
    )

    return _to_automation_response(action)