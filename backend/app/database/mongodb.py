import logging
from typing import Optional
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manages asynchronous MongoDB connection lifecycle and collection access."""

    def __init__(self) -> None:
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[AsyncDatabase] = None
        self._connected: bool = False

    async def connect(self, uri: str, db_name: str) -> None:
        """Establish async connection to MongoDB Atlas or local MongoDB."""
        try:
            logger.info("Connecting to MongoDB at %s ...", uri.split("@")[-1] if "@" in uri else uri)
            self.client = AsyncMongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            self.db = self.client[db_name]
            # Verify connectivity
            await self.client.admin.command("ping")
            self._connected = True
            logger.info("Successfully connected to MongoDB database: %s", db_name)
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as exc:
            self._connected = False
            logger.warning(
                "Could not establish live MongoDB connection during startup: %s. "
                "The server will continue, but database calls will fail until connectivity is restored.",
                str(exc),
            )

    async def close(self) -> None:
        """Close MongoDB client connection pool."""
        if self.client:
            logger.info("Closing MongoDB connection pool...")
            await self.client.close()
            self.client = None
            self.db = None
            self._connected = False

    async def ping(self) -> bool:
        """Check if MongoDB connection is active and responsive."""
        if not self.client:
            return False
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    @property
    def users(self) -> AsyncCollection:
        """Access 'users' collection."""
        if self.db is None:
            raise RuntimeError("Database not initialized. Please check MongoDB connection.")
        return self.db["users"]

    @property
    def conversations(self) -> AsyncCollection:
        """Access 'conversations' collection."""
        if self.db is None:
            raise RuntimeError("Database not initialized. Please check MongoDB connection.")
        return self.db["conversations"]

    @property
    def messages(self) -> AsyncCollection:
        """Access 'messages' collection."""
        if self.db is None:
            raise RuntimeError("Database not initialized. Please check MongoDB connection.")
        return self.db["messages"]


# Global database manager instance
mongodb_manager = MongoDBManager()
