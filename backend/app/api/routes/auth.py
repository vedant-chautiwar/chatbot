from typing import Any, Dict
from fastapi import APIRouter, Depends, status

from app.auth.security import AuthenticatedUser
from app.dependencies import get_current_user
from app.models.user import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.user_service import user_service
from app.utils.object_id import serialize_mongo_doc

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(payload: UserRegisterRequest) -> TokenResponse:
    """
    Register a new user account with validated email and password.
    Hashes password securely and stores in MongoDB.
    Returns access token and user profile.
    """
    user_doc, token = await user_service.register_user(
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )
    serialized = serialize_mongo_doc(user_doc)
    user_resp = UserResponse(
        id=serialized["id"],
        email=serialized["email"],
        name=serialized.get("name"),
        role=serialized.get("role", "user"),
        created_at=serialized["created_at"],
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain access token",
)
async def login(payload: UserLoginRequest) -> TokenResponse:
    """
    Authenticate user with email and password.
    Returns signed JWT access token upon successful credentials verification.
    """
    user_doc, token = await user_service.authenticate_user(
        email=payload.email,
        password=payload.password,
    )
    serialized = serialize_mongo_doc(user_doc)
    user_resp = UserResponse(
        id=serialized["id"],
        email=serialized["email"],
        name=serialized.get("name"),
        role=serialized.get("role", "user"),
        created_at=serialized["created_at"],
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.get("/me", summary="Get authenticated user identity")
async def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return verified identity details for the authenticated user."""
    # Look up full profile in MongoDB if available
    db_user = await user_service.get_user_by_id(current_user.user_id)
    if db_user:
        serialized = serialize_mongo_doc(db_user)
        return {
            "id": serialized["id"],
            "user_id": serialized["id"],
            "email": serialized["email"],
            "name": serialized.get("name"),
            "role": serialized.get("role", "user"),
            "created_at": serialized.get("created_at"),
        }

    return {
        "id": current_user.user_id,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.post("/logout", summary="Logout current session")
async def logout(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Client-side session termination confirmation."""
    return {"message": "Logged out successfully", "user_id": current_user.user_id}
