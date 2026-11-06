from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    id: str = Field(description="Unique document identifier")
    user_id: str = Field(description="Owner user identifier")
    conversation_id: Optional[str] = Field(default=None, description="Associated conversation identifier")
    filename: str = Field(description="Original file name")
    file_type: str = Field(description="File extension without dot, e.g. pdf, txt, md, py")
    category: str = Field(description="Document category: 'document' or 'code'")
    file_size: int = Field(description="File size in bytes")
    chunk_count: int = Field(default=0, description="Number of extracted chunks indexed in vector store")
    status: str = Field(default="ready", description="Processing status: 'ready', 'processing', 'failed'")
    error_message: Optional[str] = Field(default=None, description="Error detail if status is failed")
    created_at: str = Field(description="ISO 8601 creation timestamp")


class DocumentUploadResponse(BaseModel):
    message: str = Field(default="Document uploaded and indexed successfully")
    document: DocumentMetadata


class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    user_id: str
    filename: str
    page_number: Optional[int] = None
    chunk_index: int
    content: str
    score: Optional[float] = None

