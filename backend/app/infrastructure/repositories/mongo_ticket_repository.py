from pymongo.database import Database

from app.application.ports.ticket_repository import TicketRepository
from app.domain.ticket import Ticket


class MongoTicketRepository(TicketRepository):
    """MongoDB persistence adapter for tickets."""

    COLLECTION_NAME = "tickets"

    def __init__(
        self,
        database: Database,
    ) -> None:
        self._collection = database[
            self.COLLECTION_NAME
        ]

    def save(
        self,
        ticket: Ticket,
    ) -> Ticket:
        document = ticket.model_dump(
            mode="json"
        )

        self._collection.replace_one(
            {
                "ticket_id": ticket.ticket_id
            },
            document,
            upsert=True,
        )

        return ticket

    def get_by_id(
        self,
        ticket_id: str,
    ) -> Ticket | None:
        document = self._collection.find_one(
            {
                "ticket_id": ticket_id
            }
        )

        if document is None:
            return None

        document.pop(
            "_id",
            None,
        )

        return Ticket.model_validate(
            document
        )

    def list_by_user(
        self,
        user_id: str,
    ) -> list[Ticket]:
        cursor = self._collection.find(
            {
                "user_id": user_id
            }
        ).sort(
            "created_at",
            -1,
        )

        tickets: list[Ticket] = []

        for document in cursor:
            document.pop(
                "_id",
                None,
            )

            tickets.append(
                Ticket.model_validate(
                    document
                )
            )

        return tickets

    def list_all(
        self,
    ) -> list[Ticket]:
        """
        Retrieve all tickets ordered newest first.

        The dashboard performs its own deterministic recent-ticket
        ordering, but returning newest-first here is also useful for
        repository consumers.
        """

        cursor = self._collection.find(
            {}
        ).sort(
            "created_at",
            -1,
        )

        tickets: list[Ticket] = []

        for document in cursor:
            document.pop(
                "_id",
                None,
            )

            tickets.append(
                Ticket.model_validate(
                    document
                )
            )

        return tickets