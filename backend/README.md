# ChautiBot 2.0 — Backend Service

A production-minded, asynchronous backend for ChautiBot 2.0 featuring autonomous multi-branch intent routing, live web search, local RAG-based document analysis, and a specialized code assistant. Built using **FastAPI**, **LangGraph**, **Groq LLM**, **PyMuPDF**, **FastEmbed**, **FAISS**, **Tavily Search API**, and **MongoDB Atlas** with native JWT authentication.

---

## 1. Architecture Overview

The backend implements an intelligent multi-branch agentic workflow using **LangGraph** where incoming requests are dynamically routed based on conversation context, attached documents, and user intent:

```
                           +----------------------+
                           |   Client / Frontend  |
                           +----------+-----------+
                                      |
                     Bearer Token     |  HTTP REST / SSE
                                      v
                           +----------------------+
                           | FastAPI (Port 8000)  |
                           +----------+-----------+
                                      |
            +-------------------------+-------------------------+
            |                         |                         |
            v                         v                         v
+--------------------+      +--------------------+     +-------------------+
|  Native JWT Auth   |      | MongoDB Atlas      |     | LangGraph Router  |
|  PBKDF2 Hashing    |      | Collections:       |     | StateGraph:       |
|  (HS256 Bearer)    |      | - users            |     | - Router Node     |
|  User Ownership    |      | - conversations    |     | - RAG Node        |
+--------------------+      | - messages         |     | - Code Node       |
                            | - documents        |     | - Agent & Tools   |
                            +--------------------+     +---------+---------+
                                                                 |
              +-----------------------+--------------------------+-----------------------+
              |                       |                          |                       |
              v                       v                          v                       v
   +--------------------+  +--------------------+     +--------------------+  +--------------------+
   |  Local Vector RAG  |  |   Code Assistant   |     |   Tavily Search    |  |  Direct Response   |
   |  PyMuPDF + FAISS   |  |   AST & Heuristics |     |   Web Grounding    |  |  Foundational LLM  |
   +--------------------+  +--------------------+     +--------------------+  +--------------------+
```

### Key Workflow Behaviors

1. **Document Analysis Queries** (e.g., *"Summarize this uploaded PDF"*, *"What are the key terms on page 4?"*):
   - The router identifies active `document_ids` or document references.
   - User-isolated FAISS indices perform cosine similarity retrieval against chunk embeddings (`bge-small-en-v1.5`).
   - Relevant chunks with page numbers and source metadata are fed to the document synthesis prompt.
   - Sources are serialized into the SSE stream with verified page numbers.
2. **Code Assistance Queries** (e.g., *"Debug this Python script"*, *"Analyze the time complexity of this code"*):
   - Language is auto-detected from filename or syntax heuristics (9+ languages).
   - Dedicated code assistant prompt generates structured explanations, root-cause bug diagnoses, complexity analyses, and unit tests.
   - Static analysis only; user code is never executed.
3. **Current or External Verification Queries** (e.g., *"Give me the latest AI news"*, *"What happened in tech today?"*):
   - The agent invokes `tavily_search` with a targeted query.
   - Web results are normalized and sanitized.
   - Real publication dates and domain metadata are attributed to sources.
4. **General Conceptual Queries** (e.g., *"What is an LLM?"*, *"Explain gradient descent"*):
   - Answered directly from the foundational model without unnecessary search or vector retrieval.

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entrypoint, CORS, lifespan, exception handlers
│   ├── config.py                # Pydantic Settings centralized configuration
│   ├── dependencies.py          # FastAPI dependencies (auth verification, database injection)
│   ├── api/
│   │   ├── router.py            # Consolidated /api router
│   │   └── routes/
│   │       ├── health.py        # GET /api/health (service & dependency health)
│   │       ├── auth.py          # POST /api/auth/register, /login, /logout, GET /me
│   │       ├── chat.py          # POST /api/chat, POST /api/chat/stream (SSE)
│   │       ├── conversations.py # CRUD /api/conversations
│   │       └── documents.py     # POST /api/documents/upload, GET, DELETE /api/documents
│   ├── agents/
│   │   ├── graph.py             # LangGraph StateGraph definition and compilation
│   │   ├── state.py             # AgentState with message reducer and deduplicating source merger
│   │   ├── nodes.py             # Router, RAG, Code Assistant, call_model, and execute_tools nodes
│   │   ├── prompts.py           # Specialized system prompts (general, document RAG, code assistant)
│   │   └── tools.py             # Tavily search LangChain tool with schema validation
│   ├── services/
│   │   ├── chat_service.py      # Bounded history loader, agent runner, message persistence, SSE streaming
│   │   ├── conversation_service.py # Conversation metadata, user ownership validation, cascade deletion
│   │   ├── document_service.py  # Document validation, PyMuPDF extraction, chunking, and persistence
│   │   ├── document_retrieval.py # FastEmbed provider, FAISS vector indexer and semantic search
│   │   ├── code_assistant.py    # Code language detection, extraction, and prompt construction
│   │   ├── search_service.py    # Tavily API client, query sanitization, date validation, domain parsing
│   │   └── user_service.py      # User registration, authentication, and retrieval
│   ├── database/
│   │   ├── mongodb.py           # Asynchronous MongoDB manager using pymongo.AsyncMongoClient
│   │   └── indexes.py           # Indexes for fast user queries, documents, and ownership enforcement
│   ├── auth/
│   │   └── security.py          # PBKDF2-HMAC-SHA256 password hashing & HS256 JWT access tokens
│   ├── models/
│   │   ├── user.py              # UserRegistrationRequest, UserLoginRequest, UserResponse
│   │   ├── chat.py              # ChatRequest, ChatResponse, ChatMessageResponse, Source
│   │   ├── conversation.py      # ConversationCreate, ConversationUpdate, ConversationResponse
│   │   └── document.py          # DocumentMetadata, DocumentUploadResponse, DocumentChunk
│   └── utils/
│       ├── object_id.py         # MongoDB ObjectId validation & recursive JSON serialization
│       └── sse.py               # Server-Sent Events framing helper
├── tests/
│   ├── conftest.py              # Pytest fixtures, test tokens, mock DB injection
│   ├── mock_mongo.py            # Async in-memory MongoDB manager for offline deterministic tests
│   ├── test_health.py           # Health check and degraded status tests
│   ├── test_auth.py             # Registration, login, token expiry, and signature validation
│   ├── test_chat.py             # Sync chat, persistence, multi-turn, input validation, user isolation
│   ├── test_conversations.py    # Conversation CRUD, pagination, and cross-user isolation tests
│   ├── test_agent_routing.py    # Decision routing (direct vs search), tool calling, error recovery
│   ├── test_stream.py           # Server-Sent Events progressive streaming protocol tests
│   ├── test_search_service.py   # Tavily normalization, domain extraction, non-fabricated dates
│   ├── test_document_service.py # File validation, chunking, sanitization, and extraction
│   ├── test_document_retrieval.py # FastEmbed fallback, FAISS index creation, search & deletion
│   ├── test_code_assistant.py   # Language detection (9+ langs), code extraction, and prompt formatting
│   ├── test_documents_api.py    # REST endpoints: upload, list, get, delete, cross-user isolation
│   └── test_routing.py          # LangGraph router node intent classification and edge routing
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git exclusion rules
├── requirements.txt             # Pinned production dependencies
└── README.md                    # Documentation
```

---

## 3. Prerequisites & Environment Setup

- **Python**: 3.11+ (tested on Python 3.13)
- **MongoDB**: MongoDB Atlas or local MongoDB (`mongodb://localhost:27017`)
- **Groq API Key**: from [console.groq.com](https://console.groq.com)
- **Tavily Search API Key**: from [tavily.com](https://tavily.com)

### Installation

```powershell
# Create & activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
Copy-Item .env.example .env
```

### Environment Configuration (`backend/.env`)

```env
# Groq LLM
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Tavily Web Search
TAVILY_API_KEY=tvly-your_tavily_api_key_here
TAVILY_MAX_RESULTS=5
TAVILY_SEARCH_DEPTH=basic

# MongoDB Database
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=chatbot_db

# FastAPI Authentication
JWT_SECRET=your_super_secret_jwt_key_at_least_32_characters_long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application Settings
FRONTEND_ORIGIN=http://localhost:3000,http://localhost:5173
ENVIRONMENT=development
MAX_HISTORY_MESSAGES=10

# Document & Vector Storage Settings (optional defaults)
DOCUMENT_STORAGE_DIR=storage/documents
VECTOR_STORAGE_DIR=storage/vectors
MAX_DOCUMENT_SIZE_MB=15
```

---

## 4. Document Processing & Local RAG Pipeline

```
[ Upload File ] ➔ [ Validation: size <= 15MB, extension, magic bytes ]
                ➔ [ Text Extraction: PyMuPDF for PDF, utf-8 for TXT/MD/Code ]
                ➔ [ Chunking: 750-char window, 120-char overlap, page metadata ]
                ➔ [ Embedding: FastEmbed BAAI/bge-small-en-v1.5 (384-dim) ]
                ➔ [ Vector Storage: Local FAISS IndexFlatIP (storage/vectors/<user_id>/<doc_id>.faiss) ]
                ➔ [ Retrieval: Cosine similarity search on query embedding ]
                ➔ [ Grounded Synthesis: Groq LLM with cited page numbers ]
```

- **Per-User Isolation**: Vector indices and raw files are stored strictly under `storage/vectors/<user_id>/` and `storage/documents/<user_id>/`.
- **Offline / Resilient Embeddings**: If FastEmbed model weights are not cached locally, the service automatically falls back to an internal deterministic embedding provider to maintain continuity during tests and offline development.
- **Cascade Cleanup**: Deleting a document removes its FAISS index file, chunk metadata JSON, raw file on disk, and MongoDB document record.

---

## 5. Code Assistant Pipeline

- **Supported Languages**: Python, C, C++, Java, JavaScript, TypeScript, HTML, CSS, SQL.
- **Language Detection**: Automatically determined via file extensions or multi-language heuristic pattern matching (shebangs, imports, keyword frequency).
- **Static Analysis Only**: Code is analyzed strictly through static text/AST heuristics and the Groq reasoning model. Code is **never** executed, compiled, or evaluated on the server.
- **Capabilities**:
  - Detailed explanations of unfamiliar syntax, functions, and architecture.
  - Root-cause debugging of syntax/logic errors and runtime stack traces.
  - Time & space algorithmic complexity estimation.
  - Code refactoring and comprehensive unit test generation.

---

## 6. API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user account with email & password |
| `POST` | `/api/auth/login` | Authenticate user and receive signed JWT access token |
| `GET` | `/api/auth/me` | Retrieve profile of the authenticated user |
| `POST` | `/api/auth/logout` | Terminate user session |

### Documents & Attachments (New in 2.0)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload & index PDF, TXT, MD, or source file (multipart/form-data) |
| `GET` | `/api/documents` | List authenticated user's uploaded documents |
| `GET` | `/api/documents/{id}` | Retrieve document metadata, chunk count, and processing status |
| `DELETE` | `/api/documents/{id}` | Delete document file, FAISS vector index, and MongoDB record |

### Chat & Streaming
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/stream` | Progressive SSE streaming chat endpoint with LangGraph agent status and token streaming (supports `document_ids`) |
| `POST` | `/api/chat` | Synchronous fallback chat endpoint (supports `document_ids`) |

#### SSE Event Protocol
The stream delivers continuous JSON-encoded frames in standard SSE format:
`event: <event_name>\ndata: <json_string>\n\n`

| Event | Description | Payload Example |
| :--- | :--- | :--- |
| `meta` | Dispatched immediately with identifiers | `{"conversation_id": "...", "assistant_message_id": "..."}` |
| `status` | Public activity status | `{"status": "thinking"}` or `{"status": "searching"}` or `{"status": "analyzing"}` or `{"status": "generating"}` |
| `token` | Incremental generated answer text | `{"token": "The summary of section 2 is: "}` |
| `sources` | Final validated source citations | `{"sources": [{"title": "report.pdf", "url": null, "page_number": 3, "document_id": "..."}]}` |
| `done` | Generation completed successfully | `{"conversation_id": "...", "assistant_message_id": "...", "status": "completed"}` |
| `error` | Safe, user-facing error message | `{"detail": "..."}` |

### Conversations
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/conversations` | List user's conversations with pagination (`limit`, `offset`) |
| `POST` | `/api/conversations` | Create a new conversation session |
| `GET` | `/api/conversations/{id}` | Retrieve conversation metadata and ordered message history |
| `PATCH` | `/api/conversations/{id}` | Rename conversation title |
| `DELETE` | `/api/conversations/{id}` | Delete conversation and cascade delete its messages |

### Health
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and MongoDB connectivity check |
| `GET` | `/` | Root service status and documentation link |

---

## 7. Automated Tests

The backend includes a comprehensive test suite of **131 tests** covering unit, integration, RAG, and LangGraph routing workflows:

```powershell
pytest tests -v
# Output: 131 passed in ~2.5s
```

### Test Coverage Highlights:
- **`test_document_service.py`**: Filename sanitization, directory traversal defense, file type categorization, sliding-window chunking, PyMuPDF extraction, size limits, and invalid PDF rejection.
- **`test_document_retrieval.py`**: FastEmbed embedding normalization, fallback embedder, FAISS IndexFlatIP creation, cosine similarity search, and index deletion.
- **`test_code_assistant.py`**: Language detection across 9+ programming languages, code block extraction, and prompt formatting.
- **`test_documents_api.py`**: Upload multipart endpoint, document listing, metadata retrieval, cascade deletion, and cross-user ownership isolation.
- **`test_routing.py`**: LangGraph router node intent classification (General Chat, Web Search, Document Analysis, Code Assistance) and graph conditional edge routing.
- **`test_agent_routing.py`**: Direct answer vs. Tavily search tool execution and error recovery.
- **`test_auth.py`**: Registration, login, password hashing, JWT signature verification, and expired token rejection.
- **`test_chat.py` & `test_stream.py`**: Synchronous and SSE streaming chat persistence, multi-turn history, and input validation.

---

## 8. Security Hardening

1. **Strict User Ownership**:
   - The user ID is **always** extracted from the verified JWT (`sub` claim). Client-supplied user IDs are never trusted.
   - All conversation, message, and document queries filter strictly by `user_id`. Attempting to access another user's resource returns `404 Not Found` without leaking data existence.
2. **Multi-Tenant Vector Isolation**:
   - FAISS vector indices are stored in user-scoped directories (`storage/vectors/<user_id>/`). Users cannot query or retrieve document chunks from another user's index.
3. **File Upload Security**:
   - File size enforced at 15 MB boundary.
   - Whitelist validation for extensions.
   - PDF magic-byte header inspection (`%PDF-`) to reject disguised executables.
   - Filename sanitization stripping path separators to prevent directory traversal.
4. **Zero Code Execution**:
   - Source code submitted by users is strictly analyzed statically. No code is executed, interpreted, or compiled on the server.
5. **Untrusted Web Data Grounding**:
   - Retrieved web content and document chunks are enclosed within system delimiters to prevent prompt injection attacks.
6. **No Hallucinated Dates or Page Numbers**:
   - Sources include real, verified page numbers or search publication dates; values are omitted rather than fabricated if missing.
