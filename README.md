# ChautiBot 2.0 — Agentic AI Chatbot with Document Analysis, Code Assistant & Web Search

A full-stack, production-grade conversational AI assistant inspired by **ChatGPT** and **Gemini**. The application features an intelligent multi-modal **LangGraph** agent workflow that dynamically classifies user intent into **General Chat**, **Web Search** (via Tavily), **Document Analysis** (RAG via PyMuPDF + FastEmbed + FAISS), or **Code Assistance** (explaining, debugging, complexity analysis, and generating code for 9+ programming languages), backed by **FastAPI** JWT authentication and persistent storage in **MongoDB**.

---

## 🌟 Key Features

- **Document Analysis & Local RAG (New in 2.0)**:
  - Upload documents directly via the message composer paperclip button or drag-and-drop.
  - Supported formats: **PDF (`.pdf`)**, **Plain Text (`.txt`)**, and **Markdown (`.md`)**.
  - High-performance text extraction using **PyMuPDF** preserving page numbers and source metadata.
  - Overlapping sliding-window chunking (750 chars, 120 overlap).
  - High-efficiency local embeddings powered by **FastEmbed** (`BAAI/bge-small-en-v1.5`, 384 dimensions) with deterministic fallback.
  - Per-user isolated **FAISS** vector indexing for fast semantic retrieval without leaking data between accounts.
  - Grounded answer synthesis citing verified page numbers and chunk metadata.
  - Supported queries: summaries, section breakdown, concept explanation, key date/figure extraction, cross-document comparison, and follow-up Q&A.

- **Dedicated Code Assistant (New in 2.0)**:
  - Paste code directly or upload source files in **Python, C, C++, Java, JavaScript, TypeScript, HTML, CSS, SQL**.
  - Automatic language detection from file extensions and code structure heuristics.
  - Dedicated code reasoning node providing:
    - **Code Explanation**: execution flow, function & class breakdown, library idioms.
    - **Debugging & Error Diagnosis**: syntax & logic error identification with concrete fixes.
    - **Optimization & Best Practices**: time/space complexity analysis, edge case identification, refactored snippets.
    - **Code Generation & Test Suites**: idiomatic implementations with comprehensive test cases.
  - Indentation-preserving syntax-highlighted code blocks with one-click copy.
  - Strict security guarantee: user-provided code is never executed on the host system.

- **Intelligent Request Routing (LangGraph)**:
  - Bounded multi-turn conversational memory extracted chronologically from MongoDB.
  - Autonomous intent router routing each request into:
    - **`GENERAL_CHAT`**: Foundational knowledge, creative writing, conceptual discussions.
    - **`WEB_SEARCH`**: Breaking news, current factual queries, real-time web verification via Tavily.
    - **`DOCUMENT_ANALYSIS`**: Questions grounded in uploaded PDF, TXT, or MD documents.
    - **`CODE_ASSISTANCE`**: Code explanations, debugging, optimization, or complexity analysis.

- **ChatGPT & Gemini-Inspired User Interface**:
  - Polished dark theme crafted with **React 18**, **Vite 6**, and **Tailwind CSS 3** (pure JavaScript JSX).
  - Multi-part message composer with paperclip file attachment, drag-and-drop overlay, upload progress bar, and removal button.
  - Progressive Server-Sent Events (SSE) streaming with live status indicators (`Thinking...`, `Searching web...`, `Analyzing document...`, `Inspecting code...`).
  - GitHub-flavored Markdown rendering with syntax highlighting and source cards (web links and document page citations).
  - Searchable conversation history sidebar categorized chronologically.

- **Native FastAPI & MongoDB Authentication**:
  - User registration and login with email normalization and client/server validation.
  - Cryptographic password hashing using PBKDF2-HMAC-SHA256 (100,000 iterations, random salt).
  - Signed HS256 JWT access tokens injected into API requests via Bearer headers.
  - Strict user ownership enforcement across all conversation, document, and chat endpoints.

---

## 🏗️ Architecture & LangGraph Workflow

```
[ User Request + Optional Attachment ]
                 │
                 ▼
     [ FastAPI /api/chat/stream ]
                 │  (Validates JWT, loads history & active document IDs)
                 ▼
┌────────────────────────────────────────────────────────┐
│           LangGraph StateGraph Router                  │
│                                                        │
│                  [ Router Node ]                       │
│    (Inspects intent, attachments, code snippets)       │
│        │               │               │               │
│        ▼               ▼               ▼               ▼
│  DOCUMENT_    CODE_          WEB_            GENERAL_  │
│  ANALYSIS     ASSISTANCE     SEARCH          CHAT      │
│        │               │               │               │
│        ▼               │               ▼               │
│  [ FAISS Local ]       │        [ Tavily Search ]      │
│  [ Vector RAG  ]       │        [ Web Retrieval ]      │
│        │               │               │               │
│        ▼               ▼               ▼               │
│  [ Document    ] [ Code        ] [ Reasoning Agent   ] │
│  [ Synthesis   ] [ Assistant   ] [ & Tool Execution  ] │
│  [ LLM Node    ] [ LLM Node    ] [ LLM Node          ] │
│        │               │               │               │
└────────┼───────────────┼───────────────┼───────────────┘
         └───────────────┼───────────────┘
                         ▼
        (Server-Sent Events: meta ➔ status ➔ token ➔ sources ➔ done)
                         │
                         ▼
                [ React Frontend UI ]
                         │
                         ▼
         [ MongoDB: Messages, Sources & Documents ]
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite 6, JavaScript (JSX), Tailwind CSS 3, Lucide React, react-markdown, remark-gfm |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, python-multipart |
| **Agent / LLM** | LangGraph, LangChain, Groq API (`openai/gpt-oss-120b` / `llama-3.3-70b-versatile`) |
| **Document Processing & RAG** | PyMuPDF (fitz), FastEmbed (`bge-small-en-v1.5`), FAISS (CPU vector index) |
| **Code Assistant** | Dedicated AST-aware heuristics & Groq code reasoning node (9+ languages) |
| **Web Search** | Tavily Search API |
| **Database** | MongoDB Atlas / Local MongoDB, PyMongo Async, Motor |
| **Security** | PyJWT, PBKDF2-HMAC-SHA256 password hashing |

---

## 📁 Repository Structure

```
chatbot/
├── backend/
│   ├── app/
│   │   ├── agents/            # LangGraph workflow, router node, document RAG, code assistant, tools, state
│   │   ├── api/
│   │   │   ├── routes/        # auth.py, chat.py, conversations.py, documents.py, health.py
│   │   │   └── router.py      # Unified API router
│   │   ├── auth/              # security.py (PBKDF2 hashing, JWT access tokens)
│   │   ├── database/          # mongodb.py, indexes.py
│   │   ├── models/            # Pydantic schemas (user.py, chat.py, conversation.py, document.py)
│   │   ├── services/          # chat_service.py, document_service.py, document_retrieval.py, code_assistant.py, search_service.py
│   │   ├── utils/             # object_id.py, sse.py
│   │   ├── config.py          # Pydantic BaseSettings
│   │   ├── dependencies.py    # get_current_user, get_db
│   │   └── main.py            # FastAPI ASGI application & CORS
│   ├── tests/                 # 131 automated unit, integration & routing tests
│   ├── requirements.txt       # Python dependencies (including PyMuPDF, FastEmbed, FAISS)
│   └── .env.example           # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── api/               # client.js, auth.js, chat.js, conversations.js, documents.js
│   │   ├── components/        # chat/ (Composer with upload & drag-drop, SourceCards), sidebar/, auth/
│   │   ├── context/           # AuthContext.jsx
│   │   ├── pages/             # AuthPage.jsx, ChatPage.jsx (attachment lifecycle & SSE streaming)
│   │   ├── App.jsx            # Routing and auth guards
│   │   └── main.jsx           # Entry point
│   ├── package.json           # Dependencies and scripts
│   ├── vite.config.js         # Vite configuration with proxy and chunk splitting
│   ├── tailwind.config.js     # Dark theme design tokens
│   └── .env.example           # Frontend environment template
├── storage/                   # Local filesystem storage (gitignored)
│   ├── documents/             # Uploaded user files (<user_id>/<doc_id>_<filename>)
│   └── vectors/               # Isolated FAISS indices & chunk metadata (<user_id>/<doc_id>.faiss)
└── README.md                  # Complete documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: 3.10+ (tested on Python 3.13)
- **Node.js**: v18+ (tested on Node v22)
- **MongoDB**: MongoDB Atlas connection URI or local MongoDB (`mongodb://localhost:27017`)
- **API Keys**:
  - [Groq API Key](https://console.groq.com/)
  - [Tavily API Key](https://tavily.com/)

---

### 2. Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
Copy-Item .env.example .env
```

Edit `backend/.env` with your actual credentials:
```env
# Groq LLM
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Tavily Web Search
TAVILY_API_KEY=tvly-your_tavily_api_key_here
TAVILY_MAX_RESULTS=5
TAVILY_SEARCH_DEPTH=basic

# MongoDB Database
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=chatbot_db

# FastAPI Authentication
JWT_SECRET=your_super_secret_jwt_key_at_least_32_characters_long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application Settings
FRONTEND_ORIGIN=http://localhost:3000,http://localhost:5173
ENVIRONMENT=development
MAX_HISTORY_MESSAGES=10
```

#### Run Backend Automated Tests
```powershell
pytest tests -v
# Output: 131 passed in ~2.5s
```

#### Start FastAPI Server
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation is available at [`http://localhost:8000/docs`](http://localhost:8000/docs).

---

### 3. Frontend Setup

In a new terminal:
```powershell
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Configure environment variables
Copy-Item .env.example .env

# Run development server
npm run dev
```
Open [`http://localhost:5173`](http://localhost:5173) in your browser.

#### Build for Production
```powershell
npm run build
npm run preview
```

---

## 📡 API Endpoints

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
| `POST` | `/api/documents/upload` | Upload & index PDF, TXT, MD or source code file with multi-part progress |
| `GET` | `/api/documents` | List authenticated user's uploaded documents |
| `GET` | `/api/documents/{id}` | Retrieve document metadata, chunk count, and processing status |
| `DELETE` | `/api/documents/{id}` | Delete document file, FAISS vector index, and MongoDB record |

### Chat & Streaming
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/stream` | Progressive SSE streaming chat endpoint with LangGraph agent status and token streaming (supports `document_ids`) |
| `POST` | `/api/chat` | Synchronous fallback chat endpoint (supports `document_ids`) |

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

## 🔒 Security Best Practices Implemented

1. **Password Security**: Passwords are never stored in plaintext. They are hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and a unique cryptographic 128-bit salt per account.
2. **Access Control & Multi-Tenant Isolation**: All conversation, message, and document queries enforce strict `user_id` ownership filtering. Vector indices and raw files are isolated in user-scoped subdirectories (`storage/vectors/<user_id>/` and `storage/documents/<user_id>/`).
3. **File Upload Hardening**:
   - Strictly validates extensions (`.pdf`, `.txt`, `.md` and 10 code extensions).
   - Enforces a 15 MB file size boundary both client-side and server-side.
   - Inspects binary magic bytes (`%PDF-`) for PDF files to reject disguised or corrupt binaries.
   - Sanitizes filenames against path-traversal attacks (`os.path.basename` with alphanumeric regex).
4. **Zero Code Execution**: Uploaded and pasted source code is strictly treated as text for static AST/pattern analysis and LLM reasoning. Code is **never** executed or evaluated in the backend environment.
5. **No Secrets Exposed**: Frontend `.env` only contains the backend API URL. No database credentials, Groq keys, or Tavily keys are ever sent to client-side code.
6. **Input Sanitization**: Pydantic v2 validates all incoming bodies with length, format, and type constraints.
7. **CORS Hardening**: FastAPI is configured with explicit frontend origin whitelists.
