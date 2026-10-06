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

    database["audit_logs"].create_index(
        [("audit_id", 1)],
        unique=True,
        name="audit_id_unique",
    )