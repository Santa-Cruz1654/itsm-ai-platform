from app.application.ports.ticket_repository import TicketRepository
from app.domain.ticket import Ticket


class MemoryTicketRepository(TicketRepository):
    """In-memory ticket repository for unit testing."""

    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}

    def save(
        self,
        ticket: Ticket,
    ) -> Ticket:
        self._tickets[
            ticket.ticket_id
        ] = ticket

        return ticket

    def get_by_id(
        self,
        ticket_id: str,
    ) -> Ticket | None:
        return self._tickets.get(
            ticket_id
        )

    def list_by_user(
        self,
        user_id: str,
    ) -> list[Ticket]:
        return [
            ticket
            for ticket in self._tickets.values()
            if ticket.user_id == user_id
        ]

    def list_all(
        self,
    ) -> list[Ticket]:
        return list(
            self._tickets.values()
        )