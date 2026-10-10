from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage
import pytest
from httpx import AsyncClient

from app.models.chat import Source
from app.services.chat_service import chat_service
from tests.test_agent_routing import MockAgentGraph


@pytest.mark.asyncio
async def test_chat_creates_new_conversation(auth_client_1: AsyncClient):
    """Sending a message with null conversation_id creates a persistent conversation."""
    mock_graph = MockAgentGraph(
        responses=[AIMessage(content="An LLM is a machine learning model for natural language.")]
    )

    with patch.object(chat_service, "_graph", mock_graph):
        response = await auth_client_1.post(
            "/api/chat",
            json={"conversation_id": None, "message": "What is an LLM?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert data["conversation_id"] is not None
        assert data["message"]["role"] == "assistant"
        assert "machine learning model" in data["message"]["content"]
        assert data["message"]["sources"] == []

        # Confirm conversation and messages are persisted in DB
        conv_id = data["conversation_id"]
        detail = await auth_client_1.get(f"/api/conversations/{conv_id}")
        assert detail.status_code == 200
        conv_data = detail.json()
        assert conv_data["conversation"]["title"] == "What is an LLM?"
        assert len(conv_data["messages"]) == 2  # 1 user + 1 assistant
        assert conv_data["messages"][0]["role"] == "user"
        assert conv_data["messages"][0]["content"] == "What is an LLM?"
        assert conv_data["messages"][1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_chat_in_existing_conversation(auth_client_1: AsyncClient):
    """Sending a message with existing conversation_id appends to history."""
    conv_res = await auth_client_1.post("/api/conversations", json={"title": "Multi Turn"})
    conv_id = conv_res.json()["id"]

    mock_graph = MockAgentGraph(
        responses=[
            AIMessage(content="First answer."),
            AIMessage(content="Second answer incorporating context."),
        ]
    )

    with patch.object(chat_service, "_graph", mock_graph):
        # Turn 1
        res1 = await auth_client_1.post(
            "/api/chat",
            json={"conversation_id": conv_id, "message": "First message"},
        )
        assert res1.status_code == 200
        assert res1.json()["message"]["content"] == "First answer."

        # Turn 2
        res2 = await auth_client_1.post(
            "/api/chat",
            json={"conversation_id": conv_id, "message": "Second message"},
        )
        assert res2.status_code == 200
        assert res2.json()["message"]["content"] == "Second answer incorporating context."

        # Check total messages persisted
        detail = await auth_client_1.get(f"/api/conversations/{conv_id}")
        assert detail.status_code == 200
        assert len(detail.json()["messages"]) == 4


@pytest.mark.asyncio
async def test_chat_empty_message_validation(auth_client_1: AsyncClient):
    """Empty or whitespace-only messages are rejected with 422."""
    res_empty = await auth_client_1.post("/api/chat", json={"message": ""})
    assert res_empty.status_code == 422

    res_whitespace = await auth_client_1.post("/api/chat", json={"message": "    "})
    assert res_whitespace.status_code == 422


@pytest.mark.asyncio
async def test_chat_message_length_limit(auth_client_1: AsyncClient):
    """Messages exceeding 4000 characters are rejected with 422."""
    huge_message = "a" * 4001
    res = await auth_client_1.post("/api/chat", json={"message": huge_message})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_chat_cross_user_isolation(auth_client_1: AsyncClient, auth_client_2: AsyncClient):
    """User B cannot send messages into User A's conversation."""
    conv_res = await auth_client_1.post("/api/conversations", json={"title": "Alice Private"})
    alice_conv_id = conv_res.json()["id"]

    res_bob = await auth_client_2.post(
        "/api/chat",
        json={"conversation_id": alice_conv_id, "message": "Bob sneaking in"},
    )
    assert res_bob.status_code == 404
    assert res_bob.json()["detail"] == "Conversation not found"
