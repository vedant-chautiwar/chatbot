from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.database.mongodb import mongodb_manager
from app.models.document import DocumentChunk, DocumentMetadata
from app.services.document_retrieval import BASE_STORAGE_DIR, DOCUMENTS_DIR, document_retrieval_service
from app.utils.object_id import parse_object_id, serialize_mongo_doc

logger = logging.getLogger(__name__)

# Constants & Limits
MAX_FILE_SIZE_BYTES = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
SUPPORTED_DOC_EXTENSIONS = {".pdf", ".txt", ".md"}
SUPPORTED_CODE_EXTENSIONS = {
    ".py", ".c", ".cpp", ".h", ".hpp", ".java",
    ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".sql",
}
ALL_SUPPORTED_EXTENSIONS = SUPPORTED_DOC_EXTENSIONS | SUPPORTED_CODE_EXTENSIONS

CHUNK_SIZE = 750
CHUNK_OVERLAP = 120


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and unsafe characters."""
    base = os.path.basename(filename).strip()
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    return safe_name or "uploaded_document"


def get_file_category(extension: str) -> str:
    ext = extension.lower()
    if ext in SUPPORTED_CODE_EXTENSIONS:
        return "code"
    return "document"


class DocumentService:
    """Handles document upload, validation, extraction, chunking, and persistence."""

    def __init__(self, db_manager=None) -> None:
        self.db_manager = db_manager or mongodb_manager

    def _get_user_doc_dir(self, user_id: str) -> Path:
        user_dir = DOCUMENTS_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def chunk_text(
        self,
        text: str,
        document_id: str,
        user_id: str,
        filename: str,
        page_number: Optional[int] = None,
        start_index: int = 0,
    ) -> List[dict]:
        """Split text into overlapping chunks while preserving metadata."""
        clean_text = text.strip()
        if not clean_text:
            return []

        chunks: List[dict] = []
        text_len = len(clean_text)
        current_pos = 0
        chunk_idx = start_index

        while current_pos < text_len:
            end_pos = min(current_pos + CHUNK_SIZE, text_len)

            # Try to break at a paragraph or sentence boundary if not at end
            if end_pos < text_len:
                boundary = clean_text.rfind("\n\n", current_pos, end_pos)
                if boundary == -1 or boundary <= current_pos + CHUNK_OVERLAP:
                    boundary = clean_text.rfind("\n", current_pos, end_pos)
                if boundary == -1 or boundary <= current_pos + CHUNK_OVERLAP:
                    boundary = clean_text.rfind(". ", current_pos, end_pos)
                    if boundary != -1:
                        boundary += 1  # Include the period

                if boundary > current_pos + CHUNK_OVERLAP:
                    end_pos = boundary

            chunk_content = clean_text[current_pos:end_pos].strip()
            if chunk_content:
                chunks.append({
                    "chunk_id": f"{document_id}_{chunk_idx}",
                    "document_id": document_id,
                    "user_id": user_id,
                    "filename": filename,
                    "page_number": page_number,
                    "chunk_index": chunk_idx,
                    "content": chunk_content,
                })
                chunk_idx += 1

            if end_pos >= text_len:
                break
            current_pos = max(end_pos - CHUNK_OVERLAP, current_pos + 1)

        return chunks

    async def extract_and_chunk(
        self,
        file_path: Path,
        ext: str,
        document_id: str,
        user_id: str,
        filename: str,
    ) -> Tuple[List[dict], int]:
        """
        Extract text from file and split into chunks.
        Returns (chunks, total_character_count).
        """
        chunks: List[dict] = []
        total_chars = 0

        if ext == ".pdf":
            import pymupdf
            try:
                doc = pymupdf.open(str(file_path))
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unable to read PDF file. File may be corrupted or malformed: {str(exc)}",
                )

            if doc.is_encrypted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Encrypted or password-protected PDFs are not supported.",
                )

            page_count = len(doc)
            if page_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The provided PDF contains no pages.",
                )

            global_idx = 0
            for page_idx in range(page_count):
                page = doc[page_idx]
                page_text = page.get_text("text") or ""
                total_chars += len(page_text)
                if page_text.strip():
                    page_chunks = self.chunk_text(
                        text=page_text,
                        document_id=document_id,
                        user_id=user_id,
                        filename=filename,
                        page_number=page_idx + 1,
                        start_index=global_idx,
                    )
                    chunks.extend(page_chunks)
                    global_idx += len(page_chunks)
            doc.close()

        else:
            # Text, Markdown, or Code file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()
                except Exception as exc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to decode text file: {str(exc)}",
                    )

            total_chars = len(content)
            chunks = self.chunk_text(
                text=content,
                document_id=document_id,
                user_id=user_id,
                filename=filename,
                page_number=None,
                start_index=0,
            )

        return chunks, total_chars

    async def upload_document(
        self,
        file: UploadFile,
        user_id: str,
        conversation_id: Optional[str] = None,
    ) -> DocumentMetadata:
        """Process, validate, store, and index an uploaded document."""
        orig_name = file.filename or "uploaded_file"
        safe_name = sanitize_filename(orig_name)
        ext = os.path.splitext(safe_name)[1].lower()

        if ext not in ALL_SUPPORTED_EXTENSIONS:
            allowed_list = ", ".join(sorted(ALL_SUPPORTED_EXTENSIONS))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {allowed_list}",
            )

        # Read contents with size check
        try:
            content_bytes = await file.read()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read file: {str(exc)}",
            )

        file_size = len(content_bytes)
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {max_mb} MB.",
            )

        # Content validation
        if ext == ".pdf":
            if not content_bytes.startswith(b"%PDF-"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid PDF file format header.",
                )

        doc_oid = ObjectId()
        doc_id_str = str(doc_oid)
        category = get_file_category(ext)

        # Save to disk
        user_dir = self._get_user_doc_dir(user_id)
        saved_file_path = user_dir / f"{doc_id_str}_{safe_name}"

        try:
            with open(saved_file_path, "wb") as f:
                f.write(content_bytes)
        except Exception as exc:
            logger.error("Failed to write document to disk: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store document file on server.",
            )

        # Extract text and split into chunks
        try:
            chunks, total_chars = await self.extract_and_chunk(
                file_path=saved_file_path,
                ext=ext,
                document_id=doc_id_str,
                user_id=user_id,
                filename=safe_name,
            )
        except HTTPException:
            # Clean up saved file on validation failure
            if saved_file_path.exists():
                os.remove(saved_file_path)
            raise
        except Exception as exc:
            if saved_file_path.exists():
                os.remove(saved_file_path)
            logger.error("Text extraction failed for %s: %s", safe_name, exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not extract readable text from document: {str(exc)}",
            )

        if not chunks:
            if saved_file_path.exists():
                os.remove(saved_file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No readable text or content found in the uploaded file.",
            )

        # Generate embeddings and add to FAISS index
        try:
            chunk_count = document_retrieval_service.add_document_chunks(
                user_id=user_id,
                document_id=doc_id_str,
                chunks=chunks,
            )
        except Exception as exc:
            logger.error("Indexing failed for document %s: %s", doc_id_str, exc)
            if saved_file_path.exists():
                os.remove(saved_file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate vector embeddings for document: {str(exc)}",
            )

        # Persist document metadata in MongoDB
        now = datetime.now(timezone.utc)
        conv_oid = parse_object_id(conversation_id) if conversation_id else None

        doc_record = {
            "_id": doc_oid,
            "user_id": user_id,
            "conversation_id": conv_oid,
            "filename": safe_name,
            "file_type": ext.lstrip("."),
            "category": category,
            "file_size": file_size,
            "file_path": str(saved_file_path),
            "chunk_count": chunk_count,
            "status": "ready",
            "error_message": None,
            "created_at": now,
        }

        try:
            await self.db_manager.documents.insert_one(doc_record)
        except Exception as exc:
            logger.error("Failed to insert document into MongoDB: %s", exc)
            document_retrieval_service.delete_document(user_id, doc_id_str)
            if saved_file_path.exists():
                os.remove(saved_file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record document metadata in database.",
            )

        return DocumentMetadata(
            id=doc_id_str,
            user_id=user_id,
            conversation_id=conversation_id,
            filename=safe_name,
            file_type=ext.lstrip("."),
            category=category,
            file_size=file_size,
            chunk_count=chunk_count,
            status="ready",
            error_message=None,
            created_at=now.isoformat(),
        )

    async def list_documents(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
    ) -> List[DocumentMetadata]:
        """List documents owned by the authenticated user."""
        query: Dict[str, Any] = {"user_id": user_id}
        if conversation_id:
            conv_oid = parse_object_id(conversation_id)
            query["conversation_id"] = conv_oid

        cursor = self.db_manager.documents.find(query).sort("created_at", -1)
        docs = await cursor.to_list(length=100)

        result: List[DocumentMetadata] = []
        for d in docs:
            result.append(
                DocumentMetadata(
                    id=str(d["_id"]),
                    user_id=d["user_id"],
                    conversation_id=str(d["conversation_id"]) if d.get("conversation_id") else None,
                    filename=d["filename"],
                    file_type=d["file_type"],
                    category=d.get("category", "document"),
                    file_size=d["file_size"],
                    chunk_count=d.get("chunk_count", 0),
                    status=d.get("status", "ready"),
                    error_message=d.get("error_message"),
                    created_at=d["created_at"].isoformat() if isinstance(d["created_at"], datetime) else str(d["created_at"]),
                )
            )
        return result

    async def get_document(self, user_id: str, document_id: str) -> DocumentMetadata:
        """Retrieve document metadata by ID, enforcing user ownership."""
        doc_oid = parse_object_id(document_id)
        doc = await self.db_manager.documents.find_one({"_id": doc_oid, "user_id": user_id})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied.",
            )

        return DocumentMetadata(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            conversation_id=str(doc["conversation_id"]) if doc.get("conversation_id") else None,
            filename=doc["filename"],
            file_type=doc["file_type"],
            category=doc.get("category", "document"),
            file_size=doc["file_size"],
            chunk_count=doc.get("chunk_count", 0),
            status=doc.get("status", "ready"),
            error_message=doc.get("error_message"),
            created_at=doc["created_at"].isoformat() if isinstance(doc["created_at"], datetime) else str(doc["created_at"]),
        )

    async def delete_document(self, user_id: str, document_id: str) -> bool:
        """Delete document file, vector index, and metadata record."""
        doc_oid = parse_object_id(document_id)
        doc = await self.db_manager.documents.find_one({"_id": doc_oid, "user_id": user_id})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied.",
            )

        # 1. Remove vector index and chunks
        document_retrieval_service.delete_document(user_id, document_id)

        # 2. Remove physical file from disk
        file_path_str = doc.get("file_path")
        if file_path_str:
            path = Path(file_path_str)
            if path.exists():
                try:
                    os.remove(path)
                except OSError as exc:
                    logger.warning("Could not delete file %s: %s", path, exc)

        # 3. Delete from database
        await self.db_manager.documents.delete_one({"_id": doc_oid, "user_id": user_id})
        logger.info("Deleted document %s for user %s", document_id, user_id)
        return True


document_service = DocumentService()

