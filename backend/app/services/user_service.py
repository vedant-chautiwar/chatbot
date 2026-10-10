from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional, Tuple
from bson import ObjectId
from fastapi import HTTPException, status

from app.auth.security import create_access_token, hash_password, verify_password
from app.database.mongodb import MongoDBManager, mongodb_manager

logger = logging.getLogger(__name__)


class UserService:
    """Manages user registration, credential verification, and account persistence."""

    def __init__(self, db: Optional[MongoDBManager] = None) -> None:
        self._db = db or mongodb_manager

    @property
    def db(self) -> MongoDBManager:
        return self._db

    async def register_user(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Register a new user account with a unique normalized email.
        Hashes password securely with PBKDF2-HMAC-SHA256.
        Returns the user document and a signed JWT access token.
        """
        normalized_email = email.strip().lower()

        # Check for duplicate email
        existing = await self.db.users.find_one({"email": normalized_email})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        pwd_hash = hash_password(password)
        now = datetime.now(timezone.utc)

        user_doc = {
            "email": normalized_email,
            "password_hash": pwd_hash,
            "name": (name or "").strip() or None,
            "role": "user",
            "created_at": now,
            "updated_at": now,
        }

        result = await self.db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        token = create_access_token(
            user_id=str(result.inserted_id),
            email=normalized_email,
            role="user",
        )

        return user_doc, token

    async def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Authenticate user credentials securely.
        Returns the user document and a signed JWT access token upon successful authentication.
        """
        normalized_email = email.strip().lower()

        user_doc = await self.db.users.find_one({"email": normalized_email})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(password, user_doc.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(
            user_id=str(user_doc["_id"]),
            email=normalized_email,
            role=user_doc.get("role", "user"),
        )

        return user_doc, token

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by ObjectId or string identifier."""
        try:
            oid = ObjectId(user_id)
            doc = await self.db.users.find_one({"_id": oid})
            if doc:
                return doc
        except Exception:
            pass

        return await self.db.users.find_one({"_id": user_id})


user_service = UserService()
