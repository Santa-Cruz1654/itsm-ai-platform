from __future__ import annotations

from app.application.ports.ticket_repository import TicketRepository
from app.domain.enums import TicketStatus, TicketType


class DashboardService:
    """
    Build reviewer-facing ITSM operational metrics
    from persisted tickets.

    This service intentionally reads through the
    TicketRepository abstraction rather than accessing
    MongoDB directly.

    Current dashboard semantics:

        total_tickets
            Total persisted tickets.

        open_tickets
            Tickets whose status is OPEN.

        ai_resolved_tickets
            Currently represents RESOLVED tickets because the
            Ticket domain model does not yet persist a dedicated
            AI-resolution/source field.

        escalated_tickets
            Tickets whose status is ESCALATED.

        software_requests
            REQUEST tickets whose title follows the existing
            software-provisioning ticket naming convention.

        automation
            Deterministic counts derived from persisted tickets.
    """

    def __init__(
        self,
        *,
        ticket_repository: TicketRepository,
    ) -> None:
        self._ticket_repository = ticket_repository

    def summary(self) -> dict[str, object]:
        tickets = self._ticket_repository.list_all()

        recent_tickets = sorted(
            tickets,
            key=lambda ticket: ticket.created_at,
            reverse=True,
        )[:10]

        software_requests = [
            ticket
            for ticket in tickets
            if (
                ticket.type == TicketType.REQUEST
                and ticket.title.lower().startswith(
                    "software installation:"
                )
            )
        ]

        password_resets = [
            ticket
            for ticket in tickets
            if (
                "password"
                in f"{ticket.title} {ticket.description}".lower()
                and ticket.status == TicketStatus.RESOLVED
            )
        ]

        account_unlocks = [
            ticket
            for ticket in tickets
            if (
                any(
                    term
                    in f"{ticket.title} {ticket.description}".lower()
                    for term in (
                        "account unlock",
                        "account locked",
                        "locked account",
                    )
                )
                and ticket.status == TicketStatus.RESOLVED
            )
        ]

        return {
            "total_tickets": len(tickets),

            "open_tickets": sum(
                ticket.status == TicketStatus.OPEN
                for ticket in tickets
            ),

            # NOTE:
            # The current Ticket model has no persisted AI-resolution
            # source. Therefore this currently means "resolved tickets".
            "ai_resolved_tickets": sum(
                ticket.status == TicketStatus.RESOLVED
                for ticket in tickets
            ),

            "escalated_tickets": sum(
                ticket.status == TicketStatus.ESCALATED
                for ticket in tickets
            ),

            "software_requests": len(
                software_requests
            ),

            "automation": {
                "password_reset": len(
                    password_resets
                ),

                "account_unlock": len(
                    account_unlocks
                ),

                "software_provisioning": sum(
                    ticket.status
                    in {
                        TicketStatus.OPEN,
                        TicketStatus.RESOLVED,
                    }
                    for ticket in software_requests
                ),
            },

            "recent_tickets": recent_tickets,
        }