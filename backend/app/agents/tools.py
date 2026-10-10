import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from app.services.search_service import search_service

logger = logging.getLogger(__name__)


class TavilySearchInput(BaseModel):
    """Input parameters for tavily_search tool."""

    query: str = Field(
        ...,
        description="The targeted search query to find recent, factual, or external web information (e.g. 'latest AI news', 'recent LLM developments')",
    )
    topic: Optional[str] = Field(
        default="general",
        description="Search category: 'general' for broad web searches or 'news' for current events and recent news",
    )
    days: Optional[int] = Field(
        default=7,
        description="For news queries, number of days back to search (e.g. 3, 7, 30). Default is 7",
    )


@tool("tavily_search", args_schema=TavilySearchInput)
async def tavily_search(query: str, topic: str = "general", days: int = 7) -> str:
    """Search the web for live, real-time, recent, or externally verifiable information.

    Use when the user asks about current events, latest news, breaking updates, recent releases,
    benchmarks, company updates, or questions requiring live web evidence.
    """
    logger.info("tavily_search tool invoked with query: %s, topic: %s, days: %s", query, topic, days)
    evidence_text, _ = await search_service.search(query=query, topic=topic, days=days)
    return evidence_text


TOOLS = [tavily_search]
