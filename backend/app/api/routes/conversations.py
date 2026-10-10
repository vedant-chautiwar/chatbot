from typing import Any, Dict
from fastapi import APIRouter, Depends, Query, status

from app.auth.supabase_auth import AuthenticatedUser
from app.dependencies import get_current_user
from app.models.chat import ChatMessageResponse
from app.models.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
)
from app.services.conversation_service import conversation_service
from app.utils.object_id import serialize_mongo_doc

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=ConversationListResponse, summary="List user conversations")
async def list_conversations(
    limit: int = Query(default=20, ge=1, le=100, description="Page limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ConversationListResponse:
    """List authenticated user's conversations ordered newest first."""
    items, total = await conversation_service.list_conversations(
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
    )
    serialized_items = [
        ConversationResponse(**serialize_mongo_doc(doc)) for doc in items
    ]
    return ConversationListResponse(
        items=serialized_items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
)
async def create_conversation(
    payload: ConversationCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ConversationResponse:
    """Create a new conversation owned by the authenticated user."""
    doc = await conversation_service.create_conversation(
        user_id=current_user.user_id,
        title=payload.title,
    )
    return ConversationResponse(**serialize_mongo_doc(doc))


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation details and messages",
)
async def get_conversation(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Messages limit"),
    offset: int = Query(default=0, ge=0, description="Messages offset"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ConversationDetailResponse:
    """Fetch conversation metadata and its messages, enforcing ownership."""
    conv_doc = await conversation_service.get_conversation(
        conversation_id=conversation_id,
        user_id=current_user.user_id,
    )
    msg_docs = await conversation_service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
    )

    conv_response = ConversationResponse(**serialize_mongo_doc(conv_doc))
    msg_responses = [
        ChatMessageResponse(**serialize_mongo_doc(msg)) for msg in msg_docs
    ]

    return ConversationDetailResponse(
        conversation=conv_response,
        messages=msg_responses,
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Rename a conversation",
)
async def rename_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ConversationResponse:
    """Update title of a conversation with ownership validation."""
    updated_doc = await conversation_service.rename_conversation(
        conversation_id=conversation_id,
        user_id=current_user.user_id,
        new_title=payload.title,
    )
    return ConversationResponse(**serialize_mongo_doc(updated_doc))


@router.delete(
    "/{conversation_id}",
    summary="Delete a conversation and its messages",
)
async def delete_conversation(
    conversation_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete conversation and all its messages, enforcing user ownership."""
    await conversation_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.user_id,
    )
    return {
        "message": "Conversation deleted successfully",
        "id": conversation_id,
    }
