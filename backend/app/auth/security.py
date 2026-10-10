from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import secrets
from typing import Any, Dict, Optional
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


class AuthenticatedUser(BaseModel):
    """Represents an authenticated user resolved from a verified JWT access token."""

    user_id: str = Field(description="Unique User ID (sub claim)")
    email: Optional[str] = Field(default=None, description="User email address")
    role: Optional[str] = Field(default="user", description="User role")
    claims: Dict[str, Any] = Field(default_factory=dict, description="Decoded JWT claims")


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a cryptographically secure random salt
    and 100,000 iterations.
    Format: pbkdf2:sha256:100000$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"pbkdf2:sha256:100000${salt}${derived.hex()}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a stored PBKDF2 hash using constant-time comparison.
    """
    if not password_hash or not plain_password:
        return False

    try:
        parts = password_hash.split("$")
        if len(parts) != 3:
            return False

        header, salt, expected_hash = parts
        _, hash_name, iterations_str = header.split(":")
        iterations = int(iterations_str)

        derived = hashlib.pbkdf2_hmac(
            hash_name,
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(derived.hex(), expected_hash)
    except Exception as exc:
        logger.error("Error during password verification: %s", exc)
        return False


def create_access_token(
    user_id: str,
    email: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    secret = settings.effective_jwt_secret
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


def verify_access_token(token: str) -> AuthenticatedUser:
    """
    Verify and decode a signed JWT access token.
    Raises ExpiredSignatureError or InvalidTokenError if invalid.
    """
    if not token:
        raise InvalidTokenError("Missing token")

    secret = settings.effective_jwt_secret

    decode_options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_aud": False,  # Permissive audience to support existing and new tokens
    }

    payload = jwt.decode(
        token,
        secret,
        algorithms=[settings.JWT_ALGORITHM],
        options=decode_options,
    )

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Token missing 'sub' (user_id) claim")

    return AuthenticatedUser(
        user_id=str(sub),
        email=payload.get("email"),
        role=payload.get("role", "user"),
        claims=payload,
    )
