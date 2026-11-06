"""
Tests for document service: text extraction, chunking, and service-level operations.
No live MongoDB or FAISS — uses mocked dependencies.
"""
import io
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.document_service import (
    MAX_FILE_SIZE_BYTES,
    DocumentService,
    get_file_category,
    sanitize_filename,
)


# ---------------------------------------------------------------------------
# sanitize_filename
# ---------------------------------------------------------------------------

def test_sanitize_filename_basic():
    assert sanitize_filename("my file.pdf") == "my_file.pdf"


def test_sanitize_filename_path_traversal():
    result = sanitize_filename("../../etc/passwd")
    assert ".." not in result
    assert "/" not in result
    assert result == "passwd"


def test_sanitize_filename_empty():
    assert sanitize_filename("") == "uploaded_document"


def test_sanitize_filename_special_chars():
    result = sanitize_filename("report (2026) @Final!.pdf")
    assert result.endswith(".pdf")
    assert "(" not in result


# ---------------------------------------------------------------------------
# get_file_category
# ---------------------------------------------------------------------------

def test_get_file_category_pdf():
    assert get_file_category(".pdf") == "document"


def test_get_file_category_txt():
    assert get_file_category(".txt") == "document"


def test_get_file_category_md():
    assert get_file_category(".md") == "document"


def test_get_file_category_py():
    assert get_file_category(".py") == "code"


def test_get_file_category_js():
    assert get_file_category(".js") == "code"


def test_get_file_category_cpp():
    assert get_file_category(".cpp") == "code"


def test_get_file_category_java():
    assert get_file_category(".java") == "code"


# ---------------------------------------------------------------------------
# DocumentService.chunk_text
# ---------------------------------------------------------------------------

class TestDocumentServiceChunking:
    def setup_method(self):
        self.svc = DocumentService()

    def test_chunk_simple_text(self):
        text = "Hello world. " * 100  # ~1300 chars
        chunks = self.svc.chunk_text(
            text=text,
            document_id="doc1",
            user_id="user1",
            filename="test.txt",
        )
        assert len(chunks) >= 1
        for c in chunks:
            assert c["document_id"] == "doc1"
            assert c["user_id"] == "user1"
            assert c["filename"] == "test.txt"
            assert len(c["content"]) > 0

    def test_chunk_empty_text(self):
        chunks = self.svc.chunk_text("   ", "d1", "u1", "f.txt")
        assert chunks == []

    def test_chunk_carries_page_number(self):
        text = "Some meaningful content here. " * 20
        chunks = self.svc.chunk_text(text, "doc2", "user2", "report.pdf", page_number=3)
        assert all(c["page_number"] == 3 for c in chunks)

    def test_chunk_overlapping_indices_are_sequential(self):
        text = "Word " * 500
        chunks = self.svc.chunk_text(text, "doc3", "user3", "long.txt")
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(indices)))

    def test_chunk_long_text_produces_multiple_chunks(self):
        text = "A" * 3000
        chunks = self.svc.chunk_text(text, "docX", "userX", "big.txt")
        assert len(chunks) >= 2


# ---------------------------------------------------------------------------
# DocumentService.extract_and_chunk — text/md files
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_extract_txt_file():
    svc = DocumentService()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("This is a test document.\n" * 50)
        tmp = f.name
    try:
        chunks, total_chars = await svc.extract_and_chunk(
            file_path=Path(tmp),
            ext=".txt",
            document_id="doc_txt",
            user_id="u1",
            filename="test.txt",
        )
        assert total_chars > 0
        assert len(chunks) >= 1
        assert all(c["filename"] == "test.txt" for c in chunks)
    finally:
        try:
            os.unlink(tmp)
        except (PermissionError, OSError):
            pass


@pytest.mark.asyncio
async def test_extract_md_file():
    svc = DocumentService()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Title\n\nSome markdown content.\n" * 30)
        tmp = f.name
    try:
        chunks, total_chars = await svc.extract_and_chunk(
            file_path=Path(tmp),
            ext=".md",
            document_id="doc_md",
            user_id="u1",
            filename="readme.md",
        )
        assert total_chars > 0
        assert len(chunks) >= 1
    finally:
        try:
            os.unlink(tmp)
        except (PermissionError, OSError):
            pass


@pytest.mark.asyncio
async def test_extract_py_code_file():
    svc = DocumentService()
    code = "def hello():\n    print('world')\n\n" * 30
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp = f.name
    try:
        chunks, total_chars = await svc.extract_and_chunk(
            file_path=Path(tmp),
            ext=".py",
            document_id="doc_py",
            user_id="u1",
            filename="script.py",
        )
        assert total_chars > 0
        assert len(chunks) >= 1
    finally:
        try:
            os.unlink(tmp)
        except (PermissionError, OSError):
            pass


@pytest.mark.asyncio
async def test_extract_invalid_pdf_raises_400():
    from fastapi import HTTPException
    svc = DocumentService()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"not a real pdf file")
        tmp = f.name
    try:
        with pytest.raises(HTTPException) as exc_info:
            await svc.extract_and_chunk(
                file_path=Path(tmp),
                ext=".pdf",
                document_id="bad_pdf",
                user_id="u1",
                filename="bad.pdf",
            )
        assert exc_info.value.status_code == 400
    finally:
        try:
            os.unlink(tmp)
        except (PermissionError, OSError):
            pass


# ---------------------------------------------------------------------------
# DocumentService.upload_document — validation boundary tests via mocked DB
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_unsupported_format_rejected():
    from fastapi import HTTPException
    from unittest.mock import AsyncMock
    mock_file = MagicMock()
    mock_file.filename = "malware.exe"
    mock_file.read = AsyncMock(return_value=b"binary content")

    svc = DocumentService()
    with pytest.raises(HTTPException) as exc_info:
        await svc.upload_document(file=mock_file, user_id="user1")
    assert exc_info.value.status_code == 400
    assert ".exe" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_empty_file_rejected():
    from fastapi import HTTPException
    mock_file = MagicMock()
    mock_file.filename = "empty.pdf"
    mock_file.read = AsyncMock(return_value=b"")

    svc = DocumentService()
    with pytest.raises(HTTPException) as exc_info:
        await svc.upload_document(file=mock_file, user_id="user1")
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_upload_oversized_file_rejected():
    from fastapi import HTTPException
    mock_file = MagicMock()
    mock_file.filename = "huge.pdf"
    mock_file.read = AsyncMock(return_value=b"%PDF-" + b"x" * (MAX_FILE_SIZE_BYTES + 1))

    svc = DocumentService()
    with pytest.raises(HTTPException) as exc_info:
        await svc.upload_document(file=mock_file, user_id="user1")
    assert exc_info.value.status_code == 400
    assert "size" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_upload_fake_pdf_header_rejected():
    from fastapi import HTTPException
    mock_file = MagicMock()
    mock_file.filename = "fake.pdf"
    mock_file.read = AsyncMock(return_value=b"This is not really a PDF")

    svc = DocumentService()
    with pytest.raises(HTTPException) as exc_info:
        await svc.upload_document(file=mock_file, user_id="user1")
    assert exc_info.value.status_code == 400
    assert "PDF" in exc_info.value.detail

