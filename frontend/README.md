# Agentic AI Chatbot Frontend

A premium, ChatGPT & Gemini-inspired conversational interface built with **React 18**, **Vite 6**, **JavaScript**, and **Tailwind CSS**.

Seamlessly connected to the **FastAPI + LangGraph + Groq + Tavily + MongoDB** backend.

---

## ✨ Features

- **ChatGPT & Gemini-Grade UI**: Polished dark theme, deep obsidian palettes, subtle borders, clean typography (Inter + JetBrains Mono), smooth transitions.
- **Real-Time SSE Streaming**: Full Server-Sent Events (SSE) reader via `fetch()` and `ReadableStream` consuming `meta`, `status`, `token`, `sources`, `done`, and `error` events from FastAPI's `/api/chat/stream`.
- **Live Agentic Status Badges**: Real-time feedback displaying agent state (`Routing query...`, `Searching web with Tavily...`, `Synthesizing final answer...`).
- **Rich Markdown & Code Rendering**: Full GitHub Flavored Markdown (tables, checklists, blockquotes, lists) powered by `react-markdown` and `remark-gfm`. Code blocks include syntax badges and one-click copy.
- **Tavily Web Search Source Cards**: Interactive citation cards displaying source domain, article title, date, and expandable snippet preview.
- **Complete Conversation Management**:
  - Auto-generated conversation sessions upon initial message dispatch.
  - Automatic conversation title generation.
  - Chronological groupings in sidebar: *Today*, *Yesterday*, *Previous 7 Days*, and *Older*.
  - Inline conversation renaming.
  - Delete conversation with confirmation dialog.
  - Real-time search filter for conversation history.
  - Responsive mobile drawer sidebar.
- **FastAPI Native Authentication**:
  - Sign in and sign up with email and password via FastAPI backend (`/api/auth/register`, `/api/auth/login`).
  - Automatic JWT bearer token injection into all API requests.
  - Instant one-click Demo sign-in for testing.

---

## 🛠️ Tech Stack

- **Framework**: [React 18](https://react.dev/) + [Vite 6](https://vitejs.dev/) (pure JavaScript/JSX, no TypeScript)
- **Styling**: [Tailwind CSS 3](https://tailwindcss.com/) with custom dark design tokens (`chat-*`, `brand-*`)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Markdown**: `react-markdown`, `remark-gfm`
- **API Client**: Native `fetch` with centralized base URL configuration and JWT Bearer headers

---

## 🚀 Quick Start

### 1. Prerequisites
- **Node.js**: v18.0.0 or later (v22+ recommended)
- **npm**: v9.0.0 or later

### 2. Install Dependencies
```bash
npm install
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default content:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### 4. Run the Development Server
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 5. Production Build
```bash
npm run build
npm run preview
```
Production artifacts are generated in `dist/`.

---

## 🔌 Backend API Integration

The frontend connects directly to the FastAPI backend API:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/auth/register` | `POST` | User registration with email & password |
| `/api/auth/login` | `POST` | User login and access token issuance |
| `/api/auth/me` | `GET` | Authenticated user profile retrieval |
| `/api/auth/logout` | `POST` | User logout |
| `/api/chat/stream` | `POST` | SSE streaming chat endpoint with LangGraph agent status and token streaming |
| `/api/chat` | `POST` | Synchronous fallback chat endpoint |
| `/api/conversations` | `GET` | List user conversations with pagination (`limit`, `offset`) |
| `/api/conversations` | `POST` | Create a new conversation session |
| `/api/conversations/{id}` | `GET` | Retrieve full conversation details and message history |
| `/api/conversations/{id}` | `PATCH` | Rename conversation title |
| `/api/conversations/{id}` | `DELETE` | Delete conversation and cascade messages |

All protected requests automatically include the `Authorization: Bearer <jwt_token>` header via `src/api/client.js`.
