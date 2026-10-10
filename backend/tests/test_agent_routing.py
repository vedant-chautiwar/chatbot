import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.graph import create_agent_graph
from app.models.chat import Source
from app.services.search_service import search_service


class MockLLM:
    """Mock LangChain chat model that simulates tool calling or direct answers."""

    def __init__(self, responses: list):
        self.responses = responses
        self.call_count = 0
        self.bound_tools = []

    def bind_tools(self, tools: list):
        self.bound_tools = tools
        return self

    async def ainvoke(self, messages, *args, **kwargs):
        response = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        return response


class MockAgentGraph:
    """Mock compiled LangGraph graph that returns state dicts and yields stream events."""

    def __init__(self, responses: list, sources: list = None):
        self.responses = responses
        self.sources = sources or []
        self.call_count = 0

    async def ainvoke(self, state, *args, **kwargs):
        resp = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        messages = list(state.get("messages", []))
        messages.append(resp)
        return {
            "messages": messages,
            "sources": self.sources,
            "status": "completed",
        }

    async def astream_events(self, state, *args, **kwargs):
        resp = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        # Emit thinking status
        yield {"event": "on_tool_start", "name": "thinking", "data": {}}
        # Emit streamed token chunk
        yield {
            "event": "on_chat_model_stream",
            "name": "chat_model",
            "data": {"chunk": resp},
        }


@pytest.mark.asyncio
async def test_general_question_no_search_called():
    """
    Example A:
    User asks 'What is an LLM?'
    The agent recognizes external search is not needed.
    LLM answers directly and tavily_search is never invoked.
    """
    mock_model = MockLLM(
        responses=[
            AIMessage(
                content="A Large Language Model (LLM) is an AI neural network trained on vast text data."
            )
        ]
    )

    with patch.object(search_service, "search", new_callable=AsyncMock) as mock_search:
        graph = create_agent_graph(custom_model=mock_model)
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="What is an LLM?")],
                "sources": [],
                "status": "thinking",
            }
        )

        # Tavily search should NOT be called
        mock_search.assert_not_called()
        assert mock_model.call_count == 1
        assert len(result["sources"]) == 0
        assert "Large Language Model" in result["messages"][-1].content


@pytest.mark.asyncio
async def test_latest_news_query_invokes_search_and_attributes_sources():
    """
    Example B:
    User asks 'Give me the latest AI news.'
    1. Agent invokes tavily_search tool.
    2. Web results retrieved and normalized.
    3. LLM synthesizes grounded answer with source attribution.
    """
    mock_source = Source(
        title="OpenAI Releases New Frontier Model",
        url="https://techcrunch.com/2026/10/new-model",
        published_date="2026-10-10",
        domain="techcrunch.com",
        snippet="OpenAI today announced its new high-efficiency frontier reasoning model.",
    )

    mock_model = MockLLM(
        responses=[
            # First turn: LLM decides to call tavily_search tool
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "tavily_search",
                        "args": {"query": "latest AI news"},
                        "id": "call_mock_123",
                    }
                ],
            ),
            # Second turn: LLM synthesizes answer after receiving tool results
            AIMessage(
                content=(
                    "Here is the latest AI news: OpenAI has announced a new frontier model, "
                    "focusing on high-efficiency reasoning (TechCrunch, Oct 2026)."
                )
            ),
        ]
    )

    with patch.object(
        search_service,
        "search",
        new_callable=AsyncMock,
        return_value=("Retrieved 1 source: OpenAI Releases New Frontier Model", [mock_source]),
    ) as mock_search:
        graph = create_agent_graph(custom_model=mock_model)
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Give me the latest AI news.")],
                "sources": [],
                "status": "thinking",
            }
        )

        # Verified: Tavily search was called with targeted query
        mock_search.assert_called_once_with(query="latest AI news")
        assert mock_model.call_count == 2

        # Verified: Sources were captured in state
        sources = result.get("sources", [])
        assert len(sources) == 1
        assert sources[0]["title"] == "OpenAI Releases New Frontier Model"
        assert sources[0]["domain"] == "techcrunch.com"
        assert sources[0]["url"] == "https://techcrunch.com/2026/10/new-model"
        assert sources[0]["published_date"] == "2026-10-10"

        # Verified: Synthesized answer returned
        final_answer = result["messages"][-1].content
        assert "frontier model" in final_answer


@pytest.mark.asyncio
async def test_tool_failure_handled_gracefully():
    """Agent handles search failure gracefully without crashing."""
    mock_model = MockLLM(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "tavily_search",
                        "args": {"query": "failing query"},
                        "id": "call_err_1",
                    }
                ],
            ),
            AIMessage(
                content="I was unable to retrieve live web results, but based on general knowledge..."
            ),
        ]
    )

    with patch.object(
        search_service,
        "search",
        new_callable=AsyncMock,
        side_effect=Exception("Tavily rate limit exceeded"),
    ):
        graph = create_agent_graph(custom_model=mock_model)
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Search for recent events")],
                "sources": [],
                "status": "thinking",
            }
        )

        assert mock_model.call_count == 2
        assert "unable to retrieve live web results" in result["messages"][-1].content
