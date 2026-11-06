import json
import logging
import re
from typing import Any, Dict, List, Optional
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompts import CODE_ASSISTANT_PROMPT, DOCUMENT_ANALYSIS_PROMPT, SYSTEM_PROMPT
from app.agents.state import AgentState
from app.models.chat import Source
from app.services.code_assistant import code_assistant_service, detect_language_from_filename, extract_code_and_text
from app.services.document_retrieval import document_retrieval_service
from app.services.search_service import search_service

logger = logging.getLogger(__name__)


def _extract_tool_call_from_text(content: str) -> Optional[Dict[str, Any]]:
    """
    Parse a JSON tool call block from model text output when bind_tools is not used.
    Expected format:
      ```json
      {"tool": "tavily_search", "args": {"query": "...", "topic": "...", "days": 7}}
      ```
    """
    patterns = [
        r"```json\s*(\{.*?\})\s*```",
        r"```\s*(\{.*?\})\s*```",
        r"(\{[^{}]*\"tool\"\s*:[^{}]*\})",
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


def router_node(state: AgentState) -> Dict[str, Any]:
    """
    Intelligent Request Router:
    Classifies the user's intent into:
      - DOCUMENT_ANALYSIS
      - CODE_ASSISTANCE
      - WEB_SEARCH
      - GENERAL_CHAT
    Considers conversation history, attached document IDs, and code context.
    """
    messages = state.get("messages", [])
    uploaded_doc_ids = state.get("uploaded_document_ids") or []

    # Get latest user message content
    last_user_content = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_content = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    lower_query = last_user_content.lower()

    # 1. DOCUMENT ANALYSIS CHECK
    doc_keywords = [
        "pdf", "document", "file", "uploaded", "report", "summarize this",
        "page ", "in the text", "extract from", "compare these", "q&a based on",
        "analyze the document", "what does the doc",
    ]
    has_doc_intent = any(kw in lower_query for kw in doc_keywords)
    if uploaded_doc_ids or has_doc_intent:
        logger.info("Routing request to DOCUMENT_ANALYSIS (docs: %s, keyword match: %s)", uploaded_doc_ids, has_doc_intent)
        return {
            "request_type": "DOCUMENT_ANALYSIS",
            "status": "analyzing",
        }

    # 2. CODE ASSISTANCE CHECK
    code_keywords = [
        "code", "function", "class", "debug", "syntax error", "traceback",
        "stack trace", "time complexity", "space complexity", "big-o",
        "optimize this", "refactor", "unit test", "test cases",
        "python", "javascript", "typescript", "c++", "cpp", "java", "html", "css", "sql",
        "def ", "import ", "const ", "console.log", "int main",
    ]
    has_code_block = "```" in last_user_content
    has_code_keyword = any(kw in lower_query for kw in code_keywords)
    _, extracted_code, detected_lang = extract_code_and_text(last_user_content)

    if has_code_block or extracted_code or has_code_keyword:
        logger.info("Routing request to CODE_ASSISTANCE (detected lang: %s)", detected_lang)
        return {
            "request_type": "CODE_ASSISTANCE",
            "code_context": extracted_code,
            "detected_language": detected_lang,
            "status": "analyzing",
        }

    # 3. WEB SEARCH vs GENERAL CHAT
    search_keywords = [
        "news", "latest", "recent", "today", "yesterday", "breaking",
        "update", "release", "current", "developments", "weather",
        "price of", "who won", "live", "search for",
    ]
    if any(kw in lower_query for kw in search_keywords):
        logger.info("Routing request to WEB_SEARCH")
        return {
            "request_type": "WEB_SEARCH",
            "status": "thinking",
        }

    logger.info("Routing request to GENERAL_CHAT")
    return {
        "request_type": "GENERAL_CHAT",
        "status": "thinking",
    }


def route_request(state: AgentState) -> str:
    """Conditional router edge for LangGraph."""
    req_type = state.get("request_type", "GENERAL_CHAT")
    if req_type == "DOCUMENT_ANALYSIS":
        return "document_retrieval"
    elif req_type == "CODE_ASSISTANCE":
        return "code_assistant"
    return "agent"


def create_document_retrieval_node():
    """Retrieves document chunks from FAISS and prepares grounded context."""

    async def document_retrieval(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        messages = list(state.get("messages", []))
        user_id = state.get("user_id") or "anonymous"
        doc_ids = state.get("uploaded_document_ids")

        last_user_content = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
                last_user_content = msg.content if isinstance(msg.content, str) else str(msg.content)
                break

        query = last_user_content or "Summarize the key contents of the document"
        logger.info("Retrieving chunks for user %s, query: '%s', doc_ids: %s", user_id, query, doc_ids)

        chunks = document_retrieval_service.search(
            user_id=user_id,
            query=query,
            document_ids=doc_ids,
            top_k=6,
        )

        sources: List[Dict[str, Any]] = []
        if chunks:
            snippets = []
            for idx, c in enumerate(chunks, 1):
                fn = c.get("filename", "Document")
                pn = c.get("page_number")
                pg_str = f"Page {pn}" if pn else "N/A"
                c_text = c.get("content", "").strip()
                snippets.append(f"--- EXCERPT {idx} [{fn} | {pg_str}] ---\n{c_text}")

                sources.append({
                    "title": f"{fn} ({pg_str})" if pn else fn,
                    "url": f"#doc-{c.get('document_id')}",
                    "published_date": None,
                    "domain": fn,
                    "snippet": c_text[:300],
                    "page_number": pn,
                    "document_id": c.get("document_id"),
                })

            context_block = "\n\n".join(snippets)
            system_msg = SystemMessage(
                content=(
                    f"{DOCUMENT_ANALYSIS_PROMPT}\n\n"
                    f"### RETRIEVED DOCUMENT EXCERPTS:\n{context_block}\n\n"
                    "Ground your response strictly on the excerpts above. Cite document and page number for each claim."
                )
            )
        else:
            system_msg = SystemMessage(
                content=(
                    f"{DOCUMENT_ANALYSIS_PROMPT}\n\n"
                    "### NOTICE: No matching excerpts were found in the uploaded documents for this query.\n"
                    "Politely inform the user that the requested information could not be found in the uploaded documents, "
                    "or invite them to attach/upload the relevant document."
                )
            )

        # Prepare messages for generation: prepend our specialized system message
        dialogue_messages = [m for m in messages if not isinstance(m, SystemMessage)]
        augmented_messages = [system_msg] + dialogue_messages

        return {
            "messages": augmented_messages,
            "retrieved_document_chunks": chunks,
            "sources": sources,
            "status": "generating",
        }

    return document_retrieval


def create_code_assistant_node(model: Any):
    """Executes code analysis, explanation, debugging, and complexity assessment."""

    async def code_assistant(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        messages = list(state.get("messages", []))
        detected_lang = state.get("detected_language") or "code"

        dialogue_messages = [m for m in messages if not isinstance(m, SystemMessage)]
        system_msg = SystemMessage(content=f"{CODE_ASSISTANT_PROMPT}\nTarget Language: {detected_lang}")
        augmented_messages = [system_msg] + dialogue_messages

        logger.info("Invoking Code Assistant node with language: %s", detected_lang)
        try:
            response: AIMessage = await model.ainvoke(augmented_messages)
        except Exception as exc:
            logger.error("Error in Code Assistant node: %s", exc)
            fallback = AIMessage(
                content="I encountered an issue analyzing the provided code. Please verify the snippet and try again."
            )
            return {"messages": [fallback], "status": "completed"}

        return {
            "messages": [response],
            "status": "completed",
        }

    return code_assistant


def create_call_model_node(model: Any):
    """Factory to create call_model node for general chat and tool-calling web search."""

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

            if "model output must contain" in error_msg or "empty" in error_msg.lower():
                fallback = AIMessage(
                    content=(
                        "I apologize — I encountered a temporary model issue. "
                        "Please try again in a moment."
                    )
                )
                return {"messages": [fallback], "status": "completed"}
            raise

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

        if not native_tool_calls and content:
            parsed = _extract_tool_call_from_text(content)
            if parsed:
                logger.info("Detected prompt-embedded tool call: %s", parsed["name"])
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
            # Pass only explicit arguments to remain compatible with mock expectations
            search_kwargs: Dict[str, Any] = {"query": query}
            if "topic" in args:
                search_kwargs["topic"] = args["topic"]
            if "days" in args:
                search_kwargs["days"] = args["days"]

            try:
                evidence_text, sources = await search_service.search(**search_kwargs)
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
