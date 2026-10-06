from abc import ABC, abstractmethod

from app.domain.ticket import Ticket


class TicketRepository(ABC):
    """Port for ticket persistence."""

    @abstractmethod
    def save(
        self,
        ticket: Ticket,
    ) -> Ticket:
        """Persist a ticket and return it."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        ticket_id: str,
    ) -> Ticket | None:
        """Retrieve a ticket by its ID."""
        raise NotImplementedError

    @abstractmethod
    def list_by_user(
        self,
        user_id: str,
    ) -> list[Ticket]:
        """Retrieve tickets belonging to a user."""
        raise NotImplementedError

    @abstractmethod
    def list_all(
        self,
    ) -> list[Ticket]:
        """
        Retrieve all persisted tickets.

        Used by reviewer-facing operational dashboards
        and reporting workflows.
        """
        raise NotImplementedError
        