from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_ticket_service
from app.api.schemas.ticket import (
    CreateTicketRequest,
    TicketResponse,
)
from app.application.ticket_service import TicketService


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    request: CreateTicketRequest,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """
    Create a new ITSM incident or service request.
    """

    ticket = service.create_ticket(
        ticket_type=request.type,
        title=request.title,
        description=request.description,
        user_id=request.user_id,
    )

    return TicketResponse.model_validate(ticket)


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
async def get_ticket(
    ticket_id: str,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """
    Retrieve a ticket by ID.
    """

    ticket = service.get_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    return TicketResponse.model_validate(ticket)


@router.get(
    "",
    response_model=list[TicketResponse],
    status_code=status.HTTP_200_OK,
)
async def list_tickets(
    user_id: str,
    service: TicketService = Depends(get_ticket_service),
) -> list[TicketResponse]:
    """
    Retrieve all tickets belonging to a user.
    """

    tickets = service.list_user_tickets(user_id)

    return [
        TicketResponse.model_validate(ticket)
        for ticket in tickets
    ]