from __future__ import annotations

from app.application.ports.audit_repository import AuditRepository
from app.application.ports.ticket_repository import TicketRepository
from app.domain.enums import TicketStatus, TicketType


class DashboardService:
    """
    Build reviewer-facing ITSM operational metrics.

    Ticket metrics are derived from persisted tickets.
    Password-reset automation metrics are derived from
    persisted audit events.

    Current dashboard semantics:

        total_tickets:
            Total persisted tickets.

        open_tickets:
            Tickets whose status is OPEN.

        ai_resolved_tickets:
            Currently represents RESOLVED tickets because
            the Ticket domain model does not persist a
            dedicated AI-resolution/source field.

        escalated_tickets:
            Tickets whose status is ESCALATED.

        software_requests:
            REQUEST tickets following the existing
            software-provisioning title convention.

        password_reset:
            Number of distinct password-reset actions
            that passed automation validation and were
            not recorded as failed.

        account_unlock:
            Zero until account-unlock automation exists.

        software_provisioning:
            Number of matching software requests whose
            status is OPEN or RESOLVED.
    """

    def __init__(
        self,
        *,
        ticket_repository: TicketRepository,
        audit_repository: AuditRepository,
    ) -> None:
        self._ticket_repository = ticket_repository
        self._audit_repository = audit_repository

    def summary(self) -> dict[str, object]:
        tickets = self._ticket_repository.list_all()
        audit_events = self._audit_repository.list_all()

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

        # Identify password-reset actions from the audit trail.
        password_reset_action_ids: set[str] = set()
        validated_action_ids: set[str] = set()
        failed_action_ids: set[str] = set()

        for event in audit_events:
            action_id = event.action_id

            if not action_id:
                continue

            if (
                event.event_type == "automation_execution_started"
                and event.metadata.get("tool") == "password_reset"
            ):
                password_reset_action_ids.add(action_id)

            elif event.event_type == "automation_validated":
                validated_action_ids.add(action_id)

            elif event.event_type == "automation_failed":
                failed_action_ids.add(action_id)

        # A validated password-reset action counts once,
        # regardless of how many audit events it generated.
        # Explicit failures take precedence over validation.
        successful_password_reset_ids = (
            password_reset_action_ids
            & validated_action_ids
        ) - failed_action_ids

        password_reset_count = len(
            successful_password_reset_ids
        )

        return {
            "total_tickets": len(tickets),

            "open_tickets": sum(
                ticket.status == TicketStatus.OPEN
                for ticket in tickets
            ),

            # The model does not yet distinguish AI resolutions
            # from other resolutions.
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
                "password_reset": password_reset_count,

                # Account-unlock automation is not implemented.
                "account_unlock": 0,

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