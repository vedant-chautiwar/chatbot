# Agentic AI Chatbot with Intelligent Web Search (Backend)

A production-minded, asynchronous backend for an Agentic AI Chatbot with autonomous web search capabilities. Built using **FastAPI**, **LangGraph**, **Groq LLM**, **Tavily Search API**, **MongoDB Atlas**, and **Supabase Auth**.

---

## 1. Architecture Overview

The system implements a true agentic workflow using **LangGraph** where the model autonomously analyzes user queries and decides whether to respond directly from its foundational knowledge or retrieve real-time external evidence using the **Tavily Search API**.

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
           +--------------------------+--------------------------+
           |                          |                          |
           v                          v                          v
+--------------------+      +--------------------+     +-------------------+
|  Supabase Auth     |      | MongoDB Atlas      |     | LangGraph Agent   |
|  JWT Verification  |      | Collections:       |     | StateGraph:       |
|  (RS256 / HS256)   |      | - conversations    |     | - Agent Node      |
|  User Ownership    |      | - messages         |     | - Tools Node      |
+--------------------+      +--------------------+     +---------+---------+
                                                                 |
                                       +-------------------------+-------------------------+
                                       |                                                   |
                                       v                                                   v
                            +--------------------+                              +--------------------+
                            |   Groq Chat Model  |                              | Tavily Search API  |
                            | (llama-3.3-70b-v)  |                              | Tool & Grounding   |
                            +--------------------+                              +--------------------+
```

### Key Workflow Behaviors
1. **General Conceptual Queries** (e.g. *"What is an LLM?"*, *"Explain gradient descent"*):
   - The LangGraph agent recognizes external search is not needed.
   - Groq generates a direct response.
   - Tavily is **not** called (0 external search calls).
2. **Current or External Verification Queries** (e.g. *"Give me the latest AI news"*, *"What are the latest LangGraph releases?"*):
   - The agent invokes `tavily_search` with a targeted query.
   - Web results are normalized and sanitized (preventing prompt injections).
   - Real publication dates (never fabricated) and domain metadata are extracted.
   - Groq synthesizes a readable, grounded response citing sources.
3. **Multi-Turn Context Awareness** (e.g. *"Explain the second article in more detail"*):
   - Bounded conversation history is loaded into the agent's state.
   - The agent understands references to earlier turns and answers or executes additional targeted searches.

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
│   │       ├── auth.py          # GET /api/auth/me, POST /api/auth/logout
│   │       ├── chat.py          # POST /api/chat, POST /api/chat/stream (SSE)
│   │       └── conversations.py # CRUD /api/conversations
│   ├── agents/
│   │   ├── graph.py             # LangGraph StateGraph definition and compilation
│   │   ├── state.py             # AgentState with message reducer and deduplicating source merger
│   │   ├── nodes.py             # Agent call_model and execute_tools nodes
│   │   ├── prompts.py           # System prompts, decision rules, and grounding instructions
│   │   └── tools.py             # Tavily search LangChain tool with schema validation
│   ├── services/
│   │   ├── chat_service.py      # Bounded history loader, agent runner, message persistence, SSE streaming
│   │   ├── conversation_service.py # Conversation metadata, user ownership validation, cascade deletion
│   │   └── search_service.py    # Tavily API client, query sanitization, date validation, domain parsing
│   ├── database/
│   │   ├── mongodb.py           # Asynchronous MongoDB manager using pymongo.AsyncMongoClient
│   │   └── indexes.py           # Indexes for fast user queries and ownership enforcement
│   ├── auth/
│   │   └── supabase_auth.py     # Supabase JWT verification (asymmetric JWKS and symmetric secret)
│   ├── models/
│   │   ├── chat.py              # ChatRequest, ChatResponse, ChatMessageResponse, Source
│   │   └── conversation.py      # ConversationCreate, ConversationUpdate, ConversationResponse
│   └── utils/
│       ├── object_id.py         # MongoDB ObjectId validation & recursive JSON serialization
│       └── sse.py               # Server-Sent Events framing helper
├── tests/
│   ├── conftest.py              # Pytest fixtures, test tokens, mock DB injection
│   ├── mock_mongo.py            # Async in-memory MongoDB manager for offline deterministic tests
│   ├── test_health.py           # Health check and degraded status tests
│   ├── test_auth.py             # Missing, malformed, expired, invalid, and valid auth tests
│   ├── test_chat.py             # Sync chat, persistence, multi-turn, input validation, user isolation
│   ├── test_conversations.py    # Conversation CRUD, pagination, and cross-user isolation tests
│   ├── test_agent_routing.py    # Decision routing (direct vs search), tool calling, error recovery
│   ├── test_stream.py           # Server-Sent Events progressive streaming protocol tests
│   └── test_search_service.py   # Tavily normalization, domain extraction, non-fabricated dates
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git exclusion rules
├── requirements.txt             # Pinned production dependencies
└── README.md                    # Documentation
```

---

## 3. Prerequisites

- **Python 3.12+** (tested and verified with Python 3.13)
- **MongoDB Atlas** cluster (or local MongoDB 6.0+)
- **Supabase Project** with Authentication enabled
- **Groq Cloud API Key** (from [console.groq.com](https://console.groq.com))
- **Tavily Search API Key** (from [app.tavily.com](https://app.tavily.com))

---

## 4. Setup & Installation

### Step 1: Clone and Create Virtual Environment
```bash
cd backend
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\activate

# On Linux / macOS:
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your provider credentials:

```ini
# ==========================================
# Groq LLM Configuration
# ==========================================
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# ==========================================
# Tavily Search Configuration
# ==========================================
TAVILY_API_KEY=tvly-your_tavily_api_key_here
TAVILY_MAX_RESULTS=5
TAVILY_SEARCH_DEPTH=basic

# ==========================================
# MongoDB Atlas Database Configuration
# ==========================================
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=chatbot_db

# ==========================================
# Supabase Authentication Configuration
# ==========================================
SUPABASE_URL=https://your-project.supabase.co
# Method A: JWKS URL for RS256/ES256 (Default auto-derived from SUPABASE_URL if left blank)
SUPABASE_JWKS_URL=https://your-project.supabase.co/auth/v1/.well-known/jwks.json
# Method B: JWT Secret for HS256 projects (from Project Settings > API > JWT Secret)
SUPABASE_JWT_SECRET=your_supabase_jwt_secret_here
# Configured Algorithm (e.g., HS256, RS256, or ES256)
SUPABASE_JWT_ALGORITHM=HS256

# ==========================================
# Application & CORS Settings
# ==========================================
FRONTEND_ORIGIN=http://localhost:3000,http://localhost:5173
ENVIRONMENT=development
MAX_HISTORY_MESSAGES=10
```

---

## 5. External Services Configuration

### A. MongoDB Atlas
1. In MongoDB Atlas, create a free M0 cluster or use an existing cluster.
2. In **Database Access**, create a user with `Read and write to any database` privilege.
3. In **Network Access**, whitelist your server's IP address (or `0.0.0.0/0` during development).
4. Copy the connection string to `MONGODB_URI` in `.env`.

### B. Supabase Auth
1. In Supabase Dashboard, go to **Project Settings** > **API**.
2. Note your **Project URL** (`https://<project-ref>.supabase.co`).
3. For **HS256** projects: copy the **JWT Secret** to `SUPABASE_JWT_SECRET` and set `SUPABASE_JWT_ALGORITHM=HS256`.
4. For **RS256 / ES256** projects: set `SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json` and set `SUPABASE_JWT_ALGORITHM=RS256`.

### C. Groq LLM
1. Visit [console.groq.com/keys](https://console.groq.com/keys) and generate an API key.
2. Ensure you use a model that supports fast tool calling (default: `llama-3.3-70b-versatile` or `llama-3.1-8b-instant`).

### D. Tavily Search
1. Visit [app.tavily.com](https://app.tavily.com) and copy your API key.

---

## 6. Running the Server

Start the FastAPI application with Uvicorn:

```bash
# From the backend directory:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI documentation is automatically available in development mode at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 7. Running Automated Tests

The test suite runs with comprehensive mocks for external LLM, Search, and MongoDB services, requiring zero live credentials or network requests.

Run all tests:
```bash
pytest backend/tests -v
```

Run specific test files:
```bash
pytest backend/tests/test_agent_routing.py -v
pytest backend/tests/test_conversations.py -v
pytest backend/tests/test_chat.py -v
pytest backend/tests/test_stream.py -v
```

---

## 8. REST API Reference

All protected endpoints require the HTTP Authorization header:
```
Authorization: Bearer <supabase_access_token>
```

### Health Check
`GET /api/health`
- **Auth required**: No
- **Response**:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "environment": "development",
    "timestamp": "2026-10-10T19:49:00Z",
    "components": {
      "api": "ok",
      "database": "ok",
      "tavily_configured": true,
      "groq_configured": true
    }
  }
  ```

---

### Authentication
`GET /api/auth/me`
- **Auth required**: Yes
- **Response**:
  ```json
  {
    "user_id": "8f8b3c9a-1234-4567-89ab-cdef01234567",
    "email": "user@example.com",
    "role": "authenticated"
  }
  ```

`POST /api/auth/logout`
- **Auth required**: Yes
- **Response**: `{"message": "Logged out successfully", "user_id": "..."}`

---

### Conversations
`GET /api/conversations?limit=20&offset=0`
- **Auth required**: Yes
- **Response**: List of conversations owned by the user, newest-first.
  ```json
  {
    "items": [
      {
        "id": "670823456789abcdef012345",
        "user_id": "8f8b3c9a-1234-4567-89ab-cdef01234567",
        "title": "Latest AI news",
        "created_at": "2026-10-10T18:00:00Z",
        "updated_at": "2026-10-10T18:02:00Z",
        "last_message_preview": "Here are the top headlines...",
        "message_count": 2
      }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
  }
  ```

`POST /api/conversations`
- **Auth required**: Yes
- **Request Body**: `{"title": "Optional Custom Title"}`
- **Status**: 201 Created

`GET /api/conversations/{conversation_id}?limit=50&offset=0`
- **Auth required**: Yes
- **Response**: Full conversation details and its chronological messages.

`PATCH /api/conversations/{conversation_id}`
- **Auth required**: Yes
- **Request Body**: `{"title": "Updated Title"}`

`DELETE /api/conversations/{conversation_id}`
- **Auth required**: Yes
- **Response**: `{"message": "Conversation deleted successfully", "id": "..."}` (cascade deletes all associated messages).

---

### Chat (Synchronous)
`POST /api/chat`
- **Auth required**: Yes
- **Request Body**:
  ```json
  {
    "conversation_id": null,
    "message": "Give me the latest AI news"
  }
  ```
- **Response**:
  ```json
  {
    "conversation_id": "670823456789abcdef012345",
    "message": {
      "id": "670823456789abcdef012346",
      "conversation_id": "670823456789abcdef012345",
      "role": "assistant",
      "content": "Here is the latest AI news from today: ...",
      "sources": [
        {
          "title": "OpenAI Unveils New Model",
          "url": "https://techcrunch.com/2026/10/model",
          "published_date": "2026-10-10",
          "domain": "techcrunch.com",
          "snippet": "A new high-efficiency model was announced..."
        }
      ],
      "status": "completed",
      "created_at": "2026-10-10T18:01:00Z"
    }
  }
  ```

---

### Chat (Server-Sent Events Streaming)
`POST /api/chat/stream`
- **Auth required**: Yes
- **Headers**:
  ```
  Authorization: Bearer <access_token>
  Content-Type: application/json
  Accept: text/event-stream
  ```
- **Request Body**:
  ```json
  {
    "conversation_id": null,
    "message": "What is an LLM?"
  }
  ```

#### SSE Event Protocol
The stream delivers continuous JSON-encoded frames in the standard SSE format:
`event: <event_name>\ndata: <json_string>\n\n`

| Event | Description | Payload Example |
| :--- | :--- | :--- |
| `meta` | Dispatched immediately with identifiers | `{"conversation_id": "...", "assistant_message_id": "..."}` |
| `status` | Public activity status | `{"status": "thinking"}` or `{"status": "searching"}` or `{"status": "generating"}` |
| `token` | Incremental generated answer text | `{"token": "Large language models "}` |
| `sources` | Final validated source citations | `{"sources": [{"title": "...", "url": "...", "published_date": "...", "domain": "..."}]}` |
| `done` | Generation completed successfully | `{"conversation_id": "...", "assistant_message_id": "...", "status": "completed"}` |
| `error` | Safe, user-facing error message | `{"detail": "..."}` |

---

## 9. Security & Production Considerations

1. **Strict User Ownership**:
   - The user ID is **always** extracted from the verified Supabase JWT (`sub` claim). Client-supplied user IDs are never trusted.
   - All conversation and message operations filter strictly by `user_id`. Attempting to access another user's conversation returns `404 Not Found` without leaking data existence.
2. **Untrusted Web Data**:
   - Retrieved webpage content is marked as external untrusted evidence inside system delimiters. It cannot override system instructions or inject malicious prompts.
3. **No Hallucinated Dates or Sources**:
   - Publication dates are only populated if returned by the search provider; they are never guessed or fabricated.
4. **Bounded Conversation History**:
   - Only the latest `MAX_HISTORY_MESSAGES` dialog messages are supplied to the LLM to prevent prompt explosion and latency creep.
5. **No Secrets in Source Code**:
   - Secrets are loaded exclusively via environment variables and excluded by `.gitignore`.
