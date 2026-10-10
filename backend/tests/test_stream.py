import json
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage
import pytest
from httpx import AsyncClient

from app.services.chat_service import chat_service
from tests.test_agent_routing import MockAgentGraph


@pytest.mark.asyncio
async def test_chat_stream_sse_protocol(auth_client_1: AsyncClient):
    """
    Validates Server-Sent Events (SSE) progressive answer stream.
    Expected event sequence: meta -> status -> token -> sources -> done.
    """
    mock_graph = MockAgentGraph(
        responses=[AIMessage(content="Streamed answer chunk.")]
    )

    with patch.object(chat_service, "_graph", mock_graph):
        response = await auth_client_1.post(
            "/api/chat/stream",
            json={"conversation_id": None, "message": "Stream this test"},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        # Parse raw SSE frames
        raw_text = response.text
        lines = raw_text.split("\n")

        events_received = []
        current_event = None

        for line in lines:
            line = line.strip()
            if line.startswith("event:"):
                current_event = line.replace("event:", "").strip()
            elif line.startswith("data:") and current_event:
                data_str = line.replace("data:", "").strip()
                try:
                    payload = json.loads(data_str)
                except Exception:
                    payload = data_str
                events_received.append((current_event, payload))
                current_event = None

        event_names = [e[0] for e in events_received]

        # Verify key SSE protocol events
        assert "meta" in event_names
        assert "status" in event_names
        assert "token" in event_names
        assert "sources" in event_names
        assert "done" in event_names

        # Validate meta event payload
        meta_payload = next(payload for name, payload in events_received if name == "meta")
        assert "conversation_id" in meta_payload
        assert "assistant_message_id" in meta_payload

        # Validate done event payload
        done_payload = next(payload for name, payload in events_received if name == "done")
        assert done_payload["status"] == "completed"

        # Verify conversation and message were persisted
        conv_id = meta_payload["conversation_id"]
        detail = await auth_client_1.get(f"/api/conversations/{conv_id}")
        assert detail.status_code == 200
        assert len(detail.json()["messages"]) == 2
