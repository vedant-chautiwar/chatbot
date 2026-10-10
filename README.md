# Agentic AI Chatbot with Intelligent Web Search

A full-stack, production-grade conversational AI assistant inspired by **ChatGPT** and **Gemini**. The application features an intelligent **LangGraph** agent workflow that dynamically decides whether to answer questions directly or perform real-time web searches using **Tavily**, synthesizing evidence-grounded responses using **Groq** (Llama 3.3 70B), backed by **FastAPI** authentication and persistent conversation history stored in **MongoDB**.

---

## 🌟 Key Features

- **ChatGPT & Gemini-Inspired User Interface**:
  - Polished, responsive dark theme crafted with **React 18**, **Vite 6**, and **Tailwind CSS 3** (pure JavaScript JSX, no TypeScript).
  - Progressive Server-Sent Events (SSE) streaming for real-time token delivery with a blinking cursor.
  - Live agent status badges (`Thinking...`, `Searching web with Tavily...`, `Generating grounded answer...`).
  - Full GitHub-flavored Markdown rendering (tables, checklists, blockquotes) with code syntax cards and one-click copy.
  - Interactive Tavily citation source cards with domain badge, clickable links, and extracted snippets.
  - Searchable conversation history sidebar categorized into *Today*, *Yesterday*, *Previous 7 Days*, and *Older*.
  - Inline conversation renaming and modal deletion confirmation.
  - Auto-generated conversation titles based on the initial user message.
- **Agentic AI Workflow (LangGraph)**:
  - Bounded multi-turn conversational memory extracted chronologically from MongoDB.
  - Autonomous routing decisions:
    - **`direct_answer`**: General knowledge, coding, explanations, creative writing, mathematics without unnecessary web calls.
    - **`web_search`**: Current events, breaking news, live factual queries, or explicit search requests.
  - Real-time Tavily search integration with source normalization and date attribution.
  - Grounded answer synthesis via Groq-hosted LLM (`llama-3.3-70b-versatile`).
- **Native FastAPI & MongoDB Authentication**:
  - Secure user registration and login with email normalization and client/server validation.
  - Cryptographic password hashing using PBKDF2-HMAC-SHA256 (100,000 iterations, random salt) with constant-time comparison.
  - Signed HS256 JWT access tokens injected into API requests via Bearer headers.
  - Strict ownership enforcement across all conversation and chat endpoints.
  - No third-party auth lock-in (Supabase/Firebase free).

---

## 🏗️ Architecture & LangGraph Workflow

```
[ User Request ]
       │
       ▼
[ FastAPI /api/chat/stream ]
       │  (Extracts user identity from JWT & loads bounded history from MongoDB)
       ▼
┌────────────────────────────────────────────────────────┐
│               LangGraph Workflow State                 │
│                                                        │
│   [ Reasoning Agent Node (Groq Llama 3.3 70B) ]        │
│                         │                              │
│            Does query require live facts?              │
│            ┌────────────┴────────────┐                 │
│            ▼                         ▼                 │
│      [ No Search ]            [ Tool Calls ]           │
│     (direct_answer)                  │                 │
│            │                         ▼                 │
│            │               [ Tavily Web Search ]       │
│            │                         │                 │
│            │              (Returns grounded sources)   │
│            │                         │                 │
│            └────────────┬────────────┘                 │
│                         ▼                              │
│            [ Grounded Answer Synthesis ]               │
└────────────────────────────────────────────────────────┘
       │
       ▼  (Server-Sent Events: meta ➔ status ➔ token ➔ sources ➔ done)
[ React Frontend UI ]
       │
       ▼
[ MongoDB: Persist user message, assistant response, and sources ]
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite 6, JavaScript (JSX), Tailwind CSS 3, Lucide React, react-markdown, remark-gfm |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 |
| **Agent / LLM** | LangGraph, LangChain, Groq API (`llama-3.3-70b-versatile`) |
| **Web Search** | Tavily Search API |
| **Database** | MongoDB Atlas / Local MongoDB, PyMongo Async, Motor |
| **Security** | PyJWT, PBKDF2-HMAC-SHA256 password hashing |

---

## 📁 Repository Structure

```
chatbot/
├── backend/
│   ├── app/
│   │   ├── agents/            # LangGraph workflow, nodes, tools, prompts, state
│   │   ├── api/
│   │   │   ├── routes/        # auth.py, chat.py, conversations.py, health.py
│   │   │   └── router.py      # Unified API router
│   │   ├── auth/              # security.py (PBKDF2 hashing, JWT access tokens)
│   │   ├── database/          # mongodb.py, indexes.py
│   │   ├── models/            # Pydantic schemas (user.py, chat.py, conversation.py)
│   │   ├── services/          # chat_service.py, conversation_service.py, user_service.py, search_service.py
│   │   ├── utils/             # object_id.py, sse.py
│   │   ├── config.py          # Pydantic BaseSettings
│   │   ├── dependencies.py    # get_current_user, get_db
│   │   └── main.py            # FastAPI ASGI application & CORS
│   ├── tests/                 # 36 automated unit & integration tests
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── api/               # client.js, auth.js, chat.js, conversations.js
│   │   ├── components/        # chat/, sidebar/, auth/
│   │   ├── context/           # AuthContext.jsx
│   │   ├── pages/             # AuthPage.jsx, ChatPage.jsx
│   │   ├── App.jsx            # Routing and auth guards
│   │   └── main.jsx           # Entry point
│   ├── package.json           # Dependencies and scripts
│   ├── vite.config.js         # Vite configuration with proxy and chunk splitting
│   ├── tailwind.config.js     # Dark theme design tokens
│   └── .env.example           # Frontend environment template
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
# Output: 36 passed in ~0.7s
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

### Chat & Streaming
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/stream` | Progressive SSE streaming chat endpoint with LangGraph agent status and token streaming |
| `POST` | `/api/chat` | Synchronous fallback chat endpoint |

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
2. **Access Control**: All conversation and message queries enforce strict `user_id` ownership filtering. Attempting to access another user's conversation ID returns an HTTP 404 or 401.
3. **No Secrets Exposed**: Frontend `.env` only contains the backend API URL. No database credentials, Groq keys, or Tavily keys are ever sent to client-side code.
4. **Input Sanitization**: Pydantic v2 validates all incoming bodies with length and format constraints.
5. **CORS Hardening**: FastAPI is configured with explicit frontend origin whitelists.
