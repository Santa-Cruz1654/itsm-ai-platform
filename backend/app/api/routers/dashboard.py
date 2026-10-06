from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import get_dashboard_service
from app.api.schemas.ticket import TicketResponse
from app.application.dashboard_service import DashboardService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


class AutomationSummaryResponse(BaseModel):
    password_reset: int
    account_unlock: int
    software_provisioning: int


class DashboardSummaryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    total_tickets: int
    open_tickets: int
    ai_resolved_tickets: int
    escalated_tickets: int
    software_requests: int

    automation: AutomationSummaryResponse

    recent_tickets: list[TicketResponse]


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
def get_dashboard_summary(
    service: DashboardService = Depends(
        get_dashboard_service,
    ),
) -> DashboardSummaryResponse:
    return DashboardSummaryResponse.model_validate(
        service.summary()
    )