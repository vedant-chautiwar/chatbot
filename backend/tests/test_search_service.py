import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.services.search_service import SearchService


@pytest.mark.asyncio
async def test_search_service_empty_query():
    service = SearchService(api_key="tvly-mock-key")
    evidence, sources = await service.search(query="   ")
    assert evidence == "No query provided for search."
    assert sources == []


@pytest.mark.asyncio
async def test_search_service_unconfigured_key():
    service = SearchService(api_key="")
    evidence, sources = await service.search(query="latest AI news")
    assert "currently unavailable" in evidence
    assert sources == []


@pytest.mark.asyncio
async def test_search_service_result_normalization_and_date_handling():
    """Verify URL domain parsing and strict adherence to non-fabricated dates."""
    service = SearchService(api_key="tvly-mock-key")

    mock_raw_response = {
        "results": [
            {
                "title": "Quantum Computing Breakthrough",
                "url": "https://www.nature.com/articles/quantum-2026",
                "content": "Physicists demonstrated error mitigation.",
                "published_date": "2026-08-15",
            },
            {
                "title": "Tech Report",
                "url": "https://subdomain.tech.io/article",
                "content": "A new framework was introduced.",
                # No published_date field
            },
        ]
    }

    with patch.object(service, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.search = AsyncMock(return_value=mock_raw_response)

        evidence, sources = await service.search(query="quantum breakthrough")
        assert len(sources) == 2

        # First source
        assert sources[0].title == "Quantum Computing Breakthrough"
        assert sources[0].domain == "nature.com"  # www. stripped
        assert sources[0].published_date == "2026-08-15"

        # Second source: date must NOT be fabricated
        assert sources[1].title == "Tech Report"
        assert sources[1].domain == "subdomain.tech.io"
        assert sources[1].published_date is None


@pytest.mark.asyncio
async def test_search_service_timeout_handling():
    service = SearchService(api_key="tvly-mock-key")

    with patch.object(service, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.search = AsyncMock(side_effect=asyncio.TimeoutError)

        evidence, sources = await service.search(query="slow query")
        assert "timed out" in evidence.lower()
        assert sources == []
