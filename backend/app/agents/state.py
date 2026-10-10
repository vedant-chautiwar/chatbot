from typing import Annotated, Any, Dict, List, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def merge_sources(left: List[Dict[str, Any]], right: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reducer to merge sources across tool executions, deduplicating by URL."""
    existing_urls = {s.get("url") for s in left if s.get("url")}
    combined = list(left)
    for s in right:
        url = s.get("url")
        if not url or url not in existing_urls:
            combined.append(s)
            if url:
                existing_urls.add(url)
    return combined


class AgentState(TypedDict):
    """LangGraph agent state representation."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    sources: Annotated[List[Dict[str, Any]], merge_sources]
    status: str
