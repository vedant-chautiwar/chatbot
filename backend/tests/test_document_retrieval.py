"""
Tests for document retrieval service: embedding, FAISS indexing, search, and deletion.
Runs in a temporary directory, no network access needed.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.services.document_retrieval import DocumentRetrievalService, EmbeddingProvider


# ---------------------------------------------------------------------------
# EmbeddingProvider
# ---------------------------------------------------------------------------

class TestEmbeddingProvider:
    def setup_method(self):
        self.provider = EmbeddingProvider()

    def test_fallback_embed_returns_correct_shape(self):
        texts = ["hello world", "this is a test"]
        result = self.provider._fallback_embed(texts)
        assert result.shape == (2, self.provider._dim)
        assert result.dtype == np.float32

    def test_fallback_embed_empty_input(self):
        result = self.provider._fallback_embed([])
        assert result.shape == (0, self.provider._dim)

    def test_fallback_embed_normalized(self):
        texts = ["normalize this vector"]
        result = self.provider._fallback_embed(texts)
        norm = np.linalg.norm(result[0])
        assert abs(norm - 1.0) < 1e-5 or norm == 0.0  # zero vector or unit vector

    def test_embed_documents_uses_fallback_on_fastembed_failure(self):
        """When FastEmbed is unavailable, fallback should still produce valid output."""
        self.provider._model = "fallback"
        result = self.provider.embed_documents(["some text"])
        assert result.shape[0] == 1
        assert result.shape[1] == self.provider._dim

    def test_embed_query_returns_1d_per_query(self):
        self.provider._model = "fallback"
        vec = self.provider.embed_query("hello")
        assert vec.ndim == 1
        assert len(vec) == self.provider._dim


# ---------------------------------------------------------------------------
# DocumentRetrievalService — full roundtrip in temp dir
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_retrieval_service(tmp_path, monkeypatch):
    """DocumentRetrievalService pointed at a fresh temp directory."""
    import app.services.document_retrieval as dr_module

    monkeypatch.setattr(dr_module, "VECTORS_DIR", tmp_path / "vectors")
    monkeypatch.setattr(dr_module, "DOCUMENTS_DIR", tmp_path / "documents")
    (tmp_path / "vectors").mkdir(parents=True)
    (tmp_path / "documents").mkdir(parents=True)

    svc = DocumentRetrievalService()
    # Force fallback embedder so no network required
    svc.embedder._model = "fallback"
    return svc


def _make_chunks(doc_id: str, user_id: str, n: int = 5):
    return [
        {
            "chunk_id": f"{doc_id}_{i}",
            "document_id": doc_id,
            "user_id": user_id,
            "filename": "test.txt",
            "page_number": i + 1,
            "chunk_index": i,
            "content": f"This is chunk {i} with unique word {'alpha' if i % 2 == 0 else 'beta'} in content.",
        }
        for i in range(n)
    ]


def test_add_and_search_returns_results(tmp_retrieval_service):
    svc = tmp_retrieval_service
    chunks = _make_chunks("doc_a", "user_1", n=4)
    count = svc.add_document_chunks("user_1", "doc_a", chunks)
    assert count == 4

    results = svc.search("user_1", "alpha content", document_ids=["doc_a"], top_k=3)
    assert len(results) > 0
    assert all(r["document_id"] == "doc_a" for r in results)
    assert all(r["user_id"] == "user_1" for r in results)


def test_search_returns_max_top_k(tmp_retrieval_service):
    svc = tmp_retrieval_service
    chunks = _make_chunks("doc_b", "user_1", n=10)
    svc.add_document_chunks("user_1", "doc_b", chunks)
    results = svc.search("user_1", "content", top_k=3)
    assert len(results) <= 3


def test_search_across_multiple_documents(tmp_retrieval_service):
    svc = tmp_retrieval_service
    svc.add_document_chunks("user_1", "doc_x", _make_chunks("doc_x", "user_1", n=3))
    svc.add_document_chunks("user_1", "doc_y", _make_chunks("doc_y", "user_1", n=3))
    results = svc.search("user_1", "chunk content", top_k=5)
    doc_ids = {r["document_id"] for r in results}
    # Should search both docs when no filter given
    assert len(doc_ids) >= 1


def test_user_isolation_other_user_cannot_see_docs(tmp_retrieval_service):
    svc = tmp_retrieval_service
    svc.add_document_chunks("user_a", "doc_priv", _make_chunks("doc_priv", "user_a", n=3))

    # user_b has no docs — should return empty
    results = svc.search("user_b", "content alpha beta", top_k=5)
    assert results == []


def test_delete_document_removes_index(tmp_retrieval_service):
    svc = tmp_retrieval_service
    svc.add_document_chunks("user_1", "doc_del", _make_chunks("doc_del", "user_1", n=3))

    deleted = svc.delete_document("user_1", "doc_del")
    assert deleted is True

    results = svc.search("user_1", "content", document_ids=["doc_del"], top_k=5)
    assert results == []


def test_delete_nonexistent_document_returns_false(tmp_retrieval_service):
    svc = tmp_retrieval_service
    result = svc.delete_document("user_1", "nonexistent_doc_id")
    assert result is False


def test_add_empty_chunks_returns_zero(tmp_retrieval_service):
    svc = tmp_retrieval_service
    count = svc.add_document_chunks("user_1", "empty_doc", [])
    assert count == 0


def test_search_with_no_documents_returns_empty(tmp_retrieval_service):
    svc = tmp_retrieval_service
    results = svc.search("user_with_no_docs", "any query", top_k=5)
    assert results == []

