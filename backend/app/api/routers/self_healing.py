from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from app.api.dependencies import (
    get_intent_analyzer,
    get_self_healing_service,
)
from app.api.schemas.self_healing import (
    SelfHealingRequest,
    SelfHealingResponse,
)
from app.application.intent.intent_analyzer import (
    IntentAnalyzer,
)
from app.application.self_healing_service import (
    SelfHealingWorkflowService,
)


router = APIRouter(
    prefix="/self-healing",
    tags=["Self-Healing"],
)


@router.post(
    "",
    response_model=SelfHealingResponse,
    status_code=status.HTTP_200_OK,
)
def execute_self_healing(
    request: SelfHealingRequest,
    service: SelfHealingWorkflowService = Depends(
        get_self_healing_service,
    ),
    analyzer: IntentAnalyzer = Depends(
        get_intent_analyzer,
    ),
) -> SelfHealingResponse:
    """
    Execute the controlled self-healing workflow.

    The router is intentionally thin.

    Responsibilities:

        HTTP request validation
        ↓
        Intent analysis dependency
        ↓
        Self-healing application service
        ↓
        HTTP response mapping

    It does not construct infrastructure directly.
    """

    analysis = analyzer.analyze(
        request.employee_request,
    )

    result = service.handle(
        employee_request=(
            request.employee_request
        ),
        user_id=request.user_id,
        analysis=analysis,
        consent_granted=(
            request.consent_granted
        ),
        consent_source=(
            request.consent_source
        ),
    )

    return SelfHealingResponse(
        status=result.status,
        message=result.message,
        action_id=result.action_id,
        action=result.action,
        tool=result.tool,
        diagnosis=result.diagnosis,
        knowledge_sources=(
            result.knowledge_sources
        ),
        automation_status=(
            result.automation_status
        ),
        validation_checks=(
            result.validation_checks
        ),
        ticket_id=result.ticket_id,
        external_ticket_id=(
            result.external_ticket_id
        ),
        external_ticket_number=(
            result.external_ticket_number
        ),
        audit_event_ids=(
            result.audit_event_ids
        ),
    )