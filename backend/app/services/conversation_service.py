from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from fastapi import HTTPException, status

from app.database.mongodb import MongoDBManager, mongodb_manager
from app.utils.object_id import parse_object_id

logger = logging.getLogger(__name__)


class ConversationService:
    """Service handling conversation management and message persistence."""

    def __init__(self, db: Optional[MongoDBManager] = None) -> None:
        self._db = db or mongodb_manager

    @property
    def db(self) -> MongoDBManager:
        return self._db

    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new conversation belonging strictly to the authenticated user."""
        now = datetime.now(timezone.utc)
        clean_title = (title or "New Conversation").strip()

        doc = {
            "user_id": user_id,
            "title": clean_title,
            "created_at": now,
            "updated_at": now,
            "last_message_preview": None,
            "message_count": 0,
        }

        result = await self.db.conversations.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve a conversation by ID, enforcing strict user ownership.
        Returns 404 if not found or if owned by another user.
        """
        oid = parse_object_id(conversation_id, "Conversation")
        conv = await self.db.conversations.find_one({"_id": oid, "user_id": user_id})

        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return conv

    async def list_conversations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List authenticated user's conversations with newest-first ordering and pagination."""
        query = {"user_id": user_id}
        total = await self.db.conversations.count_documents(query)

        cursor = (
            self.db.conversations.find(query)
            .sort("updated_at", -1)
            .skip(offset)
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        return items, total

    async def rename_conversation(
        self,
        conversation_id: str,
        user_id: str,
        new_title: str,
    ) -> Dict[str, Any]:
        """Rename a conversation with ownership validation."""
        oid = parse_object_id(conversation_id, "Conversation")
        now = datetime.now(timezone.utc)

        result = await self.db.conversations.find_one_and_update(
            {"_id": oid, "user_id": user_id},
            {"$set": {"title": new_title.strip(), "updated_at": now}},
            return_document=True,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return result

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str,
    ) -> bool:
        """Delete a conversation and cascade delete its associated messages."""
        oid = parse_object_id(conversation_id, "Conversation")

        # Check ownership and delete
        res = await self.db.conversations.delete_one({"_id": oid, "user_id": user_id})
        if res.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Cascade delete all messages
        await self.db.messages.delete_many({"conversation_id": oid})
        return True

    async def get_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Fetch messages for a conversation after verifying user ownership."""
        # Verifies ownership; raises 404 if invalid or unauthorized
        await self.get_conversation(conversation_id, user_id)

        oid = parse_object_id(conversation_id, "Conversation")
        cursor = (
            self.db.messages.find({"conversation_id": oid})
            .sort("created_at", 1)
            .skip(offset)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def append_message(
        self,
        conversation_id: ObjectId,
        user_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        msg_status: str = "completed",
    ) -> Dict[str, Any]:
        """Append a message document to the messages collection."""
        now = datetime.now(timezone.utc)
        doc = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "sources": sources or [],
            "status": msg_status,
            "created_at": now,
        }
        res = await self.db.messages.insert_one(doc)
        doc["_id"] = res.inserted_id
        return doc

    async def generate_title(self, message_text: str) -> str:
        """Generate a concise conversation title (3-6 words) using Groq, with deterministic fallback."""
        clean = message_text.strip().split("\n")[0].strip()
        fallback = clean[:37].strip() + ("..." if len(clean) > 37 else "")
        if not fallback:
            return "New Conversation"

        try:
            from app.config import settings
            if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("gsk_your_") and settings.ENVIRONMENT != "testing":
                import asyncio
                from app.agents.graph import get_chat_model
                model = get_chat_model()
                prompt = (
                    "Summarize the user prompt into a short 3 to 6 word title. "
                    "Do not use quotes, punctuation, or preamble. Return ONLY the title:\n\n"
                    f"{message_text[:200]}"
                )
                res = await asyncio.wait_for(model.ainvoke(prompt), timeout=3.5)
                candidate = (res.content if hasattr(res, "content") else str(res)).strip().strip('"').strip("'")
                if candidate and len(candidate) <= 60:
                    return candidate
        except Exception:
            pass

        return fallback

    async def update_conversation_meta(
        self,
        conversation_id: ObjectId,
        user_id: str,
        last_message_content: str,
        is_first_interaction: bool = False,
    ) -> Optional[str]:
        """Update conversation updated_at, preview, message_count, and initial auto-title."""
        now = datetime.now(timezone.utc)
        preview = (
            last_message_content[:97] + "..."
            if len(last_message_content) > 100
            else last_message_content
        )

        update_fields: Dict[str, Any] = {
            "updated_at": now,
            "last_message_preview": preview,
        }

        generated_title = None
        # For a brand new conversation, derive intelligent title from first message
        if is_first_interaction:
            generated_title = await self.generate_title(last_message_content)
            update_fields["title"] = generated_title

        await self.db.conversations.update_one(
            {"_id": conversation_id, "user_id": user_id},
            {
                "$set": update_fields,
                "$inc": {"message_count": 1},
            },
        )
        return generated_title


conversation_service = ConversationService()
