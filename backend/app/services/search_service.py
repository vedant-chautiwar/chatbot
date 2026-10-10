import asyncio
import logging
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from tavily import AsyncTavilyClient

from app.config import settings
from app.models.chat import Source

logger = logging.getLogger(__name__)


class SearchService:
    """Service to execute and normalize web searches using Tavily Search API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key
        self._client: Optional[AsyncTavilyClient] = None

    @property
    def effective_api_key(self) -> str:
        """Resolve active Tavily API key dynamically."""
        return (self.api_key or settings.TAVILY_API_KEY or "").strip().strip('"\'').strip()

    def is_configured(self) -> bool:
        """Check if Tavily API key is validly configured."""
        key = self.effective_api_key
        return bool(
            key
            and not key.startswith("tvly-your_")
            and not key.startswith("tvly-test_")
        )

    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        search_depth: Optional[str] = None,
        topic: Optional[str] = None,
        days: Optional[int] = None,
    ) -> Tuple[str, List[Source]]:
        """
        Executes a web search with timeout, news topic detection, and sanitization.
        Returns:
            Tuple[str, List[Source]]: (formatted evidence for LLM, structured validated sources)
        """
        clean_query = query.strip()
        if not clean_query:
            return "No query provided for search.", []

        effective_key = self.effective_api_key
        if not self.is_configured():
            logger.warning("Tavily search invoked without configured TAVILY_API_KEY.")
            return (
                "Web search is currently unavailable because the Tavily API key is not configured. "
                "Please configure a valid TAVILY_API_KEY in the .env file.",
                [],
            )

        num_results = max_results or settings.TAVILY_MAX_RESULTS
        depth = search_depth or settings.TAVILY_SEARCH_DEPTH

        # Auto-detect news topic if query indicates recent/news
        effective_topic = topic or "general"
        if effective_topic == "general":
            news_keywords = ["news", "latest", "recent", "today", "yesterday", "breaking", "update", "developments", "releases"]
            if any(kw in clean_query.lower() for kw in news_keywords):
                effective_topic = "news"

        if self._client is None or getattr(self._client, "api_key", None) != effective_key:
            self._client = AsyncTavilyClient(api_key=effective_key)

        search_kwargs: dict = {
            "query": clean_query,
            "max_results": num_results,
            "search_depth": depth,
            "include_answer": False,
        }
        if effective_topic == "news":
            search_kwargs["topic"] = "news"
            if days:
                search_kwargs["days"] = days

        try:
            # 10 second timeout on web search
            response = await asyncio.wait_for(
                self._client.search(**search_kwargs),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            logger.error("Tavily search timed out for query: %s", clean_query)
            return "Web search request timed out after 10 seconds. Please try again or rephrase your query.", []
        except Exception as exc:
            logger.error("Tavily search failed for query '%s': %s", clean_query, exc)
            err_msg = str(exc)
            if "unauthorized" in err_msg.lower() or "invalid api key" in err_msg.lower() or "401" in err_msg:
                return (
                    f"Web search failed due to an authentication error: {err_msg}. "
                    "Please ensure a valid TAVILY_API_KEY is configured in your .env file.",
                    [],
                )
            elif "rate limit" in err_msg.lower() or "429" in err_msg:
                return (
                    f"Web search failed due to rate limit: {err_msg}. The Tavily search quota has been reached.",
                    [],
                )
            return f"Web search failed: {err_msg}", []

        raw_results = response.get("results", []) if isinstance(response, dict) else []
        if not raw_results:
            return f"No relevant web search results found for query: '{clean_query}'.", []

        sources: List[Source] = []
        evidence_snippets: List[str] = []

        for idx, item in enumerate(raw_results, start=1):
            url = str(item.get("url", "")).strip()
            title = str(item.get("title", f"Result {idx}")).strip()
            content = str(item.get("content", "")).strip()

            # Sanitize domain
            domain = None
            if url:
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc.lower()
                    if domain.startswith("www."):
                        domain = domain[4:]
                except Exception:
                    domain = None

            # Only use real published_date if provided by provider; NEVER fabricate
            pub_date = item.get("published_date")
            published_date = str(pub_date).strip() if pub_date else None

            # Snippet bounded to prevent prompt bloat
            snippet = content[:600] if content else None

            # Create validated Source object
            source_obj = Source(
                title=title,
                url=url,
                published_date=published_date,
                domain=domain,
                snippet=snippet,
            )
            sources.append(source_obj)

            # Build formatted evidence for LLM prompt
            date_info = f" | Date: {published_date}" if published_date else ""
            evidence_snippets.append(
                f"[{idx}] Title: {title}\n"
                f"URL: {url}{date_info}\n"
                f"Content: {snippet}\n"
            )

        evidence_text = (
            f"Retrieved {len(sources)} web search results for '{clean_query}':\n\n"
            + "\n".join(evidence_snippets)
        )

        return evidence_text, sources


search_service = SearchService()
