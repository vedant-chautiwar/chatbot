from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.auth.security import AuthenticatedUser
from app.dependencies import get_current_user
from app.models.document import DocumentListResponse, DocumentMetadata, DocumentUploadResponse
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a document",
)
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentUploadResponse:
    """
    Upload a document (PDF, TXT, MD, or source code file).
    Validates file format, extracts text, generates vector embeddings, and stores in user-isolated FAISS index.
    """
    doc_meta = await document_service.upload_document(
        file=file,
        user_id=current_user.user_id,
        conversation_id=conversation_id,
    )
    return DocumentUploadResponse(
        message="Document uploaded and indexed successfully",
        document=doc_meta,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
)
async def list_documents(
    conversation_id: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentListResponse:
    """List documents uploaded by the current authenticated user."""
    docs = await document_service.list_documents(
        user_id=current_user.user_id,
        conversation_id=conversation_id,
    )
    return DocumentListResponse(documents=docs)


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata,
    summary="Get document metadata",
)
async def get_document(
    document_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentMetadata:
    """Retrieve document metadata by ID, ensuring user ownership."""
    return await document_service.get_document(
        user_id=current_user.user_id,
        document_id=document_id,
    )


@router.delete(
    "/{document_id}",
    summary="Delete document",
)
async def delete_document(
    document_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Delete document file, vector embeddings, and database record."""
    await document_service.delete_document(
        user_id=current_user.user_id,
        document_id=document_id,
    )
    return {"detail": "Document deleted successfully"}

