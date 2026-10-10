from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Source(BaseModel):
    title: str = Field(description="Title of the source webpage or article")
    url: str = Field(description="Full URL of the source")
    published_date: Optional[str] = Field(
        default=None,
        description="Publication date if available from search metadata (never fabricated)",
    )
    domain: Optional[str] = Field(default=None, description="Domain name extracted from URL")
    snippet: Optional[str] = Field(default=None, description="Relevant extracted snippet")


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID of an existing conversation. If null, a new conversation is created.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User message text (1-4000 characters)",
    )

    @field_validator("message")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Message cannot be empty or only whitespace")
        return trimmed


class ChatMessageResponse(BaseModel):
    id: str = Field(description="Message unique identifier")
    conversation_id: str = Field(description="Conversation identifier")
    role: str = Field(description="Role: 'user' or 'assistant'")
    content: str = Field(description="Content of the message")
    sources: List[Source] = Field(default_factory=list, description="Validated web sources used")
    status: Optional[str] = Field(default="completed", description="Status of the message")
    created_at: str = Field(description="ISO 8601 creation timestamp")


class ChatResponse(BaseModel):
    conversation_id: str
    message: ChatMessageResponse
