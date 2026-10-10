from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.auth.security import AuthenticatedUser
from app.dependencies import get_current_user
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, summary="Send message (synchronous)")
async def send_chat_message(
    payload: ChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ChatResponse:
    """
    Send a chat message to the LangGraph AI agent.
    If conversation_id is omitted or null, a new conversation is automatically created.
    The agent dynamically decides whether external Tavily web search is needed.
    """
    return await chat_service.process_chat(
        conversation_id=payload.conversation_id,
        message=payload.message,
        user_id=current_user.user_id,
    )


@router.post(
    "/stream",
    summary="Send message (Server-Sent Events progressive streaming)",
    response_description="SSE event stream with meta, status, token, sources, and done events",
)
async def send_chat_message_stream(
    payload: ChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StreamingResponse:
    """
    Stream agent response progress and tokens via Server-Sent Events (SSE).

    Event protocol:
    - meta: {"conversation_id": "...", "assistant_message_id": "..."}
    - status: {"status": "thinking" | "searching" | "generating"}
    - token: {"token": "..."}
    - sources: {"sources": [...]}
    - done: {"conversation_id": "...", "assistant_message_id": "...", "status": "completed"}
    - error: {"detail": "..."}
    """
    generator = chat_service.process_chat_stream(
        conversation_id=payload.conversation_id,
        message=payload.message,
        user_id=current_user.user_id,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
