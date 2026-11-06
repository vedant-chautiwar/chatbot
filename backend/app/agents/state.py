from typing import Annotated, Any, Dict, List, Optional, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def merge_sources(left: List[Dict[str, Any]], right: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reducer to merge sources across tool and retrieval executions, deduplicating by URL or title."""
    existing_keys = {s.get("url") or s.get("title") for s in left if (s.get("url") or s.get("title"))}
    combined = list(left)
    for s in right:
        key = s.get("url") or s.get("title")
        if not key or key not in existing_keys:
            combined.append(s)
            if key:
                existing_keys.add(key)
    return combined


class AgentState(TypedDict, total=False):
    """LangGraph agent state representation with multi-capability support."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    sources: Annotated[List[Dict[str, Any]], merge_sources]
    status: str
    request_type: Optional[str]
    uploaded_document_ids: Optional[List[str]]
    retrieved_document_chunks: Optional[List[Dict[str, Any]]]
    code_context: Optional[str]
    detected_language: Optional[str]
    user_id: Optional[str]
