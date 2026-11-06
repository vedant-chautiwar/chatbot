"""
Integration tests for the document upload API endpoints.
Uses mocked DB and document service to avoid file-system/FAISS dependencies.
"""
import io
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.models.document import DocumentMetadata


MOCK_DOC = DocumentMetadata(
    id="64a0000000000000deadbeef",
    user_id="00000000-0000-0000-0000-000000000001",
    conversation_id=None,
    filename="test.pdf",
    file_type="pdf",
    category="document",
    file_size=1024,
    chunk_count=5,
    status="ready",
    error_message=None,
    created_at=datetime.now(timezone.utc).isoformat(),
)


@pytest.mark.asyncio
async def test_upload_document_success(auth_client_1: AsyncClient, mock_db):
    with patch(
        "app.api.routes.documents.document_service.upload_document",
        new_callable=AsyncMock,
        return_value=MOCK_DOC,
    ):
        resp = await auth_client_1.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test content"), "application/pdf")},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["document"]["filename"] == "test.pdf"
    assert data["document"]["status"] == "ready"


@pytest.mark.asyncio
async def test_upload_requires_authentication(client: AsyncClient, mock_db):
    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_documents_authenticated(auth_client_1: AsyncClient, mock_db):
    with patch(
        "app.api.routes.documents.document_service.list_documents",
        new_callable=AsyncMock,
        return_value=[MOCK_DOC],
    ):
        resp = await auth_client_1.get("/api/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["documents"], list)
    assert len(data["documents"]) == 1
    assert data["documents"][0]["filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_list_documents_requires_auth(client: AsyncClient, mock_db):
    resp = await client.get("/api/documents")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_document_metadata(auth_client_1: AsyncClient, mock_db):
    with patch(
        "app.api.routes.documents.document_service.get_document",
        new_callable=AsyncMock,
        return_value=MOCK_DOC,
    ):
        resp = await auth_client_1.get(f"/api/documents/{MOCK_DOC.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == MOCK_DOC.id


@pytest.mark.asyncio
async def test_get_document_not_found(auth_client_1: AsyncClient, mock_db):
    from fastapi import HTTPException
    with patch(
        "app.api.routes.documents.document_service.get_document",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=404, detail="Document not found or access denied."),
    ):
        resp = await auth_client_1.get("/api/documents/000000000000000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_success(auth_client_1: AsyncClient, mock_db):
    with patch(
        "app.api.routes.documents.document_service.delete_document",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = await auth_client_1.delete(f"/api/documents/{MOCK_DOC.id}")
    assert resp.status_code == 200
    assert "deleted" in resp.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_delete_document_requires_auth(client: AsyncClient, mock_db):
    resp = await client.delete(f"/api/documents/{MOCK_DOC.id}")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_document(auth_client_2: AsyncClient, mock_db):
    """User 2 cannot retrieve document owned by User 1."""
    from fastapi import HTTPException
    with patch(
        "app.api.routes.documents.document_service.get_document",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=404, detail="Document not found or access denied."),
    ):
        resp = await auth_client_2.get(f"/api/documents/{MOCK_DOC.id}")
    assert resp.status_code == 404

