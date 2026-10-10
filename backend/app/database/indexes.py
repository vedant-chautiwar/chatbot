import logging
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb import MongoDBManager

logger = logging.getLogger(__name__)


async def init_indexes(db_manager: MongoDBManager) -> None:
    """Create essential performance and ownership indexes on collections."""
    if db_manager.db is None:
        logger.warning("Skipping index creation because database is not connected.")
        return

    try:
        # Index on users: unique email constraint and lookup
        await db_manager.users.create_index(
            [("email", ASCENDING)],
            name="idx_users_email_unique",
            unique=True,
            background=True,
        )

        # Index on conversations: queries by user_id sorted by updated_at descending
        await db_manager.conversations.create_index(
            [("user_id", ASCENDING), ("updated_at", DESCENDING)],
            name="idx_conversations_user_updated",
            background=True,
        )

        # Index on messages: conversation messages in chronological order
        await db_manager.messages.create_index(
            [("conversation_id", ASCENDING), ("created_at", ASCENDING)],
            name="idx_messages_conversation_created",
            background=True,
        )

        # Index on messages: user ownership and audit tracking
        await db_manager.messages.create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)],
            name="idx_messages_user_created",
            background=True,
        )

        logger.info("Successfully verified and initialized MongoDB indexes.")
    except Exception as exc:
        logger.warning("Index creation encountered an issue: %s", str(exc))
