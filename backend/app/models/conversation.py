from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.chat import ChatMessageResponse


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120, description="Optional conversation title")


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120, description="Updated conversation title")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty or only whitespace")
        return trimmed


class ConversationResponse(BaseModel):
    id: str = Field(description="Conversation ID")
    user_id: str = Field(description="Owner Supabase user UUID")
    title: str = Field(description="Conversation title")
    created_at: str = Field(description="ISO 8601 creation timestamp")
    updated_at: str = Field(description="ISO 8601 last update timestamp")
    last_message_preview: Optional[str] = Field(default=None, description="Preview of latest message")
    message_count: int = Field(default=0, description="Total number of messages")


class ConversationListResponse(BaseModel):
    items: List[ConversationResponse]
    total: int
    limit: int
    offset: int


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[ChatMessageResponse]
