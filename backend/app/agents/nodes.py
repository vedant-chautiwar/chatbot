import json
import logging
import re
from typing import Any, Dict, List, Optional
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.state import AgentState
from app.services.search_service import search_service

logger = logging.getLogger(__name__)


def _extract_tool_call_from_text(content: str) -> Optional[Dict[str, Any]]:
    """
    Parse a JSON tool call block from model text output when bind_tools is not used.
    Expected format from the system prompt:
      ```json
      {"tool": "tavily_search", "args": {"query": "...", "topic": "...", "days": 7}}
      ```
    Returns dict with 'name' and 'args' keys, or None if not found.
    """
    # Try to find a JSON block
    patterns = [
        r"```json\s*(\{.*?\})\s*```",   # fenced ```json ... ```
        r"```\s*(\{.*?\})\s*```",        # fenced ``` ... ```
        r"(\{[^{}]*\"tool\"\s*:[^{}]*\})",  # bare JSON with "tool" key
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                tool_name = data.get("tool") or data.get("name")
                args = data.get("args") or data.get("arguments") or {}
                if tool_name:
                    return {"name": tool_name, "args": args, "id": "prompt_tool_call_0"}
            except Exception:
                continue
    return None


def create_call_model_node(model: Any):
    """Factory to create call_model node with the bound model."""

    async def call_model(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        messages = list(state["messages"])

        # Ensure SystemMessage is the first message
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        logger.debug("Invoking chat model with %d messages", len(messages))
        try:
            response: AIMessage = await model.ainvoke(messages)
        except Exception as exc:
            error_msg = str(exc)
            logger.error("Error during model invocation: %s", error_msg)

            # Handle Groq "empty output" error gracefully
            if "model output must contain" in error_msg or "empty" in error_msg.lower():
                fallback = AIMessage(
                    content=(
                        "I apologize — I encountered a temporary model issue. "
                        "Please try again in a moment."
                    )
                )
                return {"messages": [fallback], "status": "completed"}
            raise

        # Guard: if model returned empty content and no tool calls, inject a safe fallback
        content = response.content if isinstance(response.content, str) else ""
        native_tool_calls = getattr(response, "tool_calls", None) or []

        if not content.strip() and not native_tool_calls:
            logger.warning("Model returned empty content and no tool calls — returning fallback.")
            fallback = AIMessage(
                content=(
                    "I'm sorry, I wasn't able to generate a response. "
                    "Please rephrase your question and try again."
                )
            )
            return {"messages": [fallback], "status": "completed"}

        # Check for prompt-embedded tool calls (when bind_tools is not used)
        if not native_tool_calls and content:
            parsed = _extract_tool_call_from_text(content)
            if parsed:
                logger.info("Detected prompt-embedded tool call: %s", parsed["name"])
                # Reconstruct an AIMessage with synthetic tool_calls
                response = AIMessage(
                    content="",
                    tool_calls=[parsed],
                )
                native_tool_calls = [parsed]

        has_tool_calls = bool(native_tool_calls)
        next_status = "searching" if has_tool_calls else "completed"

        return {
            "messages": [response],
            "status": next_status,
        }

    return call_model


async def execute_tools_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Execute tool calls requested by the model and collect source metadata."""
    messages = state["messages"]
    if not messages:
        return {"messages": [], "sources": [], "status": "completed"}

    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", []) or []

    tool_messages: List[ToolMessage] = []
    collected_sources: List[Dict[str, Any]] = []

    for call in tool_calls:
        tool_name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
        call_id = call.get("id") if isinstance(call, dict) else getattr(call, "id", None)
        raw_args = call.get("args", {}) if isinstance(call, dict) else getattr(call, "args", {})

        if isinstance(raw_args, str):
            try:
                args = json.loads(raw_args)
            except Exception:
                args = {"query": raw_args}
        elif isinstance(raw_args, dict):
            args = raw_args
        else:
            args = {"query": str(raw_args)}

        logger.info("Executing tool: %s with args: %s", tool_name, args)

        if tool_name == "tavily_search":
            query = args.get("query", "")
            topic = args.get("topic", "general")
            days = args.get("days", 7)
            try:
                evidence_text, sources = await search_service.search(
                    query=query, topic=topic, days=days
                )
                tool_messages.append(
                    ToolMessage(
                        content=evidence_text,
                        tool_call_id=call_id,
                        name=tool_name,
                    )
                )
                collected_sources.extend([s.model_dump() for s in sources])
            except Exception as exc:
                logger.error("Failed tool execution for %s: %s", tool_name, exc)
                tool_messages.append(
                    ToolMessage(
                        content=f"Error performing web search: {str(exc)}",
                        tool_call_id=call_id,
                        name=tool_name,
                    )
                )
        else:
            logger.warning("Unrecognized tool name requested: %s", tool_name)
            tool_messages.append(
                ToolMessage(
                    content=f"Tool '{tool_name}' is not recognized.",
                    tool_call_id=call_id,
                    name=tool_name or "unknown",
                )
            )

    return {
        "messages": tool_messages,
        "sources": collected_sources,
        "status": "generating",
    }


def should_continue(state: AgentState) -> str:
    """Conditional edge router: continue to tools if tool_calls exist, else END."""
    messages = state.get("messages", [])
    if not messages:
        return "__end__"

    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None)

    if tool_calls and len(tool_calls) > 0:
        return "tools"

    return "__end__"
