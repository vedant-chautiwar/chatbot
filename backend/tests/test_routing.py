"""
Tests for the extended LangGraph router node:
- Verifies DOCUMENT_ANALYSIS routing when doc IDs are present
- Verifies CODE_ASSISTANCE routing for code-bearing messages
- Verifies WEB_SEARCH routing for news/current events queries
- Verifies GENERAL_CHAT routing for simple questions
- Verifies existing general chat and web search still work (regression)
"""
import pytest
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.nodes import route_request, router_node
from app.agents.state import AgentState


def make_state(message: str, doc_ids=None, code_ctx=None) -> AgentState:
    return {
        "messages": [HumanMessage(content=message)],
        "sources": [],
        "status": "thinking",
        "uploaded_document_ids": doc_ids or [],
        "retrieved_document_chunks": None,
        "code_context": code_ctx,
        "detected_language": None,
        "user_id": "test_user",
    }


# ---------------------------------------------------------------------------
# router_node intent classification
# ---------------------------------------------------------------------------

class TestRouterNodeIntentClassification:

    def test_routes_document_analysis_with_doc_ids(self):
        state = make_state("What does this say?", doc_ids=["abc123"])
        result = router_node(state)
        assert result["request_type"] == "DOCUMENT_ANALYSIS"

    def test_routes_document_analysis_on_pdf_keyword(self):
        state = make_state("Summarize this PDF for me.")
        result = router_node(state)
        assert result["request_type"] == "DOCUMENT_ANALYSIS"

    def test_routes_document_analysis_on_document_keyword(self):
        state = make_state("Extract key points from the uploaded document.")
        result = router_node(state)
        assert result["request_type"] == "DOCUMENT_ANALYSIS"

    def test_routes_code_assistance_on_code_block(self):
        state = make_state("Review this:\n```python\ndef foo(): pass\n```")
        result = router_node(state)
        assert result["request_type"] == "CODE_ASSISTANCE"

    def test_routes_code_assistance_on_debug_keyword(self):
        state = make_state("Debug this Python function for me.")
        result = router_node(state)
        assert result["request_type"] == "CODE_ASSISTANCE"

    def test_routes_code_assistance_on_complexity_keyword(self):
        state = make_state("What is the time complexity of this algorithm?")
        result = router_node(state)
        assert result["request_type"] == "CODE_ASSISTANCE"

    def test_routes_web_search_for_news(self):
        state = make_state("What are the latest AI news today?")
        result = router_node(state)
        assert result["request_type"] == "WEB_SEARCH"

    def test_routes_general_chat_for_simple_question(self):
        state = make_state("What is machine learning?")
        result = router_node(state)
        assert result["request_type"] == "GENERAL_CHAT"

    def test_routes_general_chat_for_greeting(self):
        state = make_state("Hello, how are you?")
        result = router_node(state)
        assert result["request_type"] == "GENERAL_CHAT"


# ---------------------------------------------------------------------------
# route_request conditional edge returns correct branch names
# ---------------------------------------------------------------------------

class TestRouteRequestEdge:

    def test_document_analysis_goes_to_document_retrieval(self):
        state = make_state("Summarize PDF", doc_ids=["id1"])
        state["request_type"] = "DOCUMENT_ANALYSIS"
        assert route_request(state) == "document_retrieval"

    def test_code_assistance_goes_to_code_assistant(self):
        state = make_state("debug my code")
        state["request_type"] = "CODE_ASSISTANCE"
        assert route_request(state) == "code_assistant"

    def test_general_chat_goes_to_agent(self):
        state = make_state("hi")
        state["request_type"] = "GENERAL_CHAT"
        assert route_request(state) == "agent"

    def test_web_search_goes_to_agent(self):
        state = make_state("latest news")
        state["request_type"] = "WEB_SEARCH"
        assert route_request(state) == "agent"

