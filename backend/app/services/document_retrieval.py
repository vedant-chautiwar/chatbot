import json
import logging
import os
from pathlib import Path
from typing import Any, List, Optional
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# Base storage directories configured via settings
DOCUMENTS_DIR = Path(settings.DOCUMENT_STORAGE_DIR).resolve()
VECTORS_DIR = Path(settings.VECTOR_STORAGE_DIR).resolve()
BASE_STORAGE_DIR = DOCUMENTS_DIR.parent

VECTORS_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


class EmbeddingProvider:
    """Provides vector embeddings using FastEmbed with resilient deterministic fallback."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self.model_name = model_name
        self._model = None
        self._dim = 384  # bge-small dimension

    def _get_model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name=self.model_name)
                logger.info("FastEmbed model %s initialized successfully.", self.model_name)
            except Exception as exc:
                logger.warning("Could not initialize FastEmbed (%s). Using fallback embedder.", exc)
                self._model = "fallback"
        return self._model

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self._dim), dtype=np.float32)

        model = self._get_model()
        if model != "fallback":
            try:
                embeddings_gen = model.embed(texts)
                vectors = np.array(list(embeddings_gen), dtype=np.float32)
                # L2 normalize
                norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                return vectors / norms
            except Exception as exc:
                logger.error("FastEmbed document embedding failed: %s. Using fallback.", exc)

        return self._fallback_embed(texts)

    def embed_query(self, query: str) -> np.ndarray:
        vectors = self.embed_documents([query])
        return vectors[0]

    def _fallback_embed(self, texts: List[str]) -> np.ndarray:
        """Deterministic hashing fallback embedder ensuring functionality in offline/test environments."""
        import hashlib
        res = np.zeros((len(texts), self._dim), dtype=np.float32)
        for i, text in enumerate(texts):
            words = text.lower().split()
            if not words:
                continue
            for word in words:
                digest = hashlib.md5(word.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:2], byteorder="little") % self._dim
                res[i, idx] += 1.0
            norm = np.linalg.norm(res[i])
            if norm > 0:
                res[i] /= norm
        return res


class DocumentRetrievalService:
    """Manages user-isolated FAISS vector retrieval and chunk persistence."""

    def __init__(self) -> None:
        self.embedder = EmbeddingProvider()

    def _get_user_vector_dir(self, user_id: str) -> Path:
        user_dir = VECTORS_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def add_document_chunks(
        self,
        user_id: str,
        document_id: str,
        chunks: List[dict],
    ) -> int:
        """
        Embeds document chunks and saves an isolated FAISS index and metadata.
        Returns the number of indexed chunks.
        """
        if not chunks:
            return 0

        import faiss

        user_dir = self._get_user_vector_dir(user_id)
        index_file = user_dir / f"{document_id}.faiss"
        meta_file = user_dir / f"{document_id}_chunks.json"

        texts = [c["content"] for c in chunks]
        vectors = self.embedder.embed_documents(texts)

        dimension = vectors.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product on normalized vectors = cosine similarity
        index.add(vectors)

        faiss.write_index(index, str(index_file))
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        logger.info("Indexed %d chunks for document %s (user %s)", len(chunks), document_id, user_id)
        return len(chunks)

    def search(
        self,
        user_id: str,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[dict]:
        """
        Retrieve the most relevant chunks scoped strictly to the authenticated user.
        If document_ids is specified, only those documents are searched.
        """
        import faiss

        user_dir = self._get_user_vector_dir(user_id)
        if not user_dir.exists():
            return []

        # Find target document index files
        if document_ids:
            target_ids = [d for d in document_ids if (user_dir / f"{d}.faiss").exists()]
        else:
            target_ids = [
                f.name[:-6]
                for f in user_dir.glob("*.faiss")
            ]

        if not target_ids:
            return []

        query_vec = self.embedder.embed_query(query).reshape(1, -1)
        all_candidates: List[dict] = []

        for doc_id in target_ids:
            index_file = user_dir / f"{doc_id}.faiss"
            meta_file = user_dir / f"{doc_id}_chunks.json"

            if not index_file.exists() or not meta_file.exists():
                continue

            try:
                index = faiss.read_index(str(index_file))
                with open(meta_file, "r", encoding="utf-8") as f:
                    chunks_meta = json.load(f)

                k = min(top_k, len(chunks_meta))
                if k == 0:
                    continue

                distances, indices = index.search(query_vec, k)

                for score, idx in zip(distances[0], indices[0]):
                    if idx >= 0 and idx < len(chunks_meta):
                        chunk = dict(chunks_meta[idx])
                        chunk["score"] = float(score)
                        all_candidates.append(chunk)
            except Exception as exc:
                logger.error("Error reading index for doc %s: %s", doc_id, exc)

        # Sort all candidates across documents by cosine similarity score descending
        all_candidates.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return all_candidates[:top_k]

    def delete_document(self, user_id: str, document_id: str) -> bool:
        """Permanently delete vector index and chunk metadata for a document."""
        user_dir = self._get_user_vector_dir(user_id)
        index_file = user_dir / f"{document_id}.faiss"
        meta_file = user_dir / f"{document_id}_chunks.json"

        removed = False
        if index_file.exists():
            try:
                os.remove(index_file)
                removed = True
            except OSError as exc:
                logger.warning("Failed to remove index file %s: %s", index_file, exc)

        if meta_file.exists():
            try:
                os.remove(meta_file)
                removed = True
            except OSError as exc:
                logger.warning("Failed to remove meta file %s: %s", meta_file, exc)

        return removed


document_retrieval_service = DocumentRetrievalService()

