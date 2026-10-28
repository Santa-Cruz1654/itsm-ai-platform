from pymongo.database import Database


def create_indexes(database: Database) -> None:
    """Create application MongoDB indexes."""

    database["tickets"].create_index(
        [("ticket_id", 1)],
        unique=True,
        name="ticket_id_unique",
    )

    database["tickets"].create_index(
        [("user_id", 1), ("created_at", -1)],
        name="tickets_by_user_created_at",
    )

    database["conversations"].create_index(
        [("conversation_id", 1)],
        unique=True,
        name="conversation_id_unique",
    )

    database["audit_events"].create_index(
        [("event_id", 1)],
        unique=True,
        name="event_id_unique",
    )