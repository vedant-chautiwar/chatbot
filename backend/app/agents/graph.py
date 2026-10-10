import logging
from typing import Any, Optional
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from app.agents.nodes import create_call_model_node, execute_tools_node, should_continue
from app.agents.state import AgentState
from app.agents.tools import TOOLS
from app.config import settings

logger = logging.getLogger(__name__)

# Models that natively support bind_tools / function calling on Groq
NATIVE_TOOL_MODELS = {
    "llama-3.1-8b-instant",
    "llama-3.1-70b-versatile",
    "llama3-8b-8192",
    "llama3-70b-8192",
    "llama-3.3-70b-specdec",
    "llama-3.3-70b-versatile",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
    "openai/gpt-oss-120b",  # Supports native function calling via Groq OpenAI-compat endpoint
}


def get_chat_model(model_name: Optional[str] = None, api_key: Optional[str] = None) -> Any:
    """Create ChatGroq instance."""
    resolved_key = (api_key or settings.GROQ_API_KEY or "").strip().strip('"\'').strip()
    resolved_model = model_name or settings.GROQ_MODEL

    if not resolved_key or resolved_key.startswith("gsk_your_"):
        if settings.ENVIRONMENT == "testing":
            resolved_key = "gsk_dummy_test_key_for_unit_tests"
        else:
            raise ValueError(
                "GROQ_API_KEY is not configured. Please set a valid GROQ_API_KEY in your .env file."
            )

    logger.info("Using Groq model: %s", resolved_model)
    return ChatGroq(
        model=resolved_model,
        groq_api_key=resolved_key,
        temperature=0.2,
        max_retries=2,
        timeout=60.0,
    )


def create_agent_graph(custom_model: Optional[Any] = None) -> Any:
    """
    Constructs and compiles the LangGraph agent workflow.
    For models that support native tool calling, binds tools directly.
    For others (e.g. openai/gpt-oss-120b), passes the raw model and uses
    prompt-based tool dispatch to avoid empty-response errors.
    """
    if custom_model is not None:
        raw_model = custom_model
    else:
        raw_model = get_chat_model()

    resolved_model = settings.GROQ_MODEL

    # Only bind tools for models that natively support function calling
    if resolved_model in NATIVE_TOOL_MODELS:
        logger.info("Binding tools natively for model: %s", resolved_model)
        bound_model = raw_model.bind_tools(TOOLS)
    else:
        logger.info(
            "Model '%s' does not support native bind_tools — using prompt-based tool routing.",
            resolved_model,
        )
        bound_model = raw_model  # No bind_tools; tool calls handled via prompt + JSON parsing

    call_model_node = create_call_model_node(bound_model)

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model_node)
    workflow.add_node("tools", execute_tools_node)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    workflow.add_edge("tools", "agent")

    return workflow.compile()
