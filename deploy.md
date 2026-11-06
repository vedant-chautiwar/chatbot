# 🚀 Deployment Guide — ChautiBot 2.0

| Layer | Platform | URL (after deploy) |
|---|---|---|
| **Backend** | [Render](https://render.com) | `https://chatbot-api-xxxx.onrender.com` |
| **Frontend** | [Vercel](https://vercel.com) | `https://chatbot-xxxx.vercel.app` |
| **Database** | [MongoDB Atlas](https://cloud.mongodb.com) | Cloud-hosted |

> **ChautiBot 2.0 Update**: Now includes **Document Analysis** (PDF, TXT, MD text extraction, FastEmbed embeddings & FAISS vector search) and a dedicated **Code Assistant** (9+ languages).

---

## ✅ Pre-Deployment Checklist

Complete these steps **before** touching Render or Vercel.

### 1. MongoDB Atlas (Free Tier)
1. Go to [https://cloud.mongodb.com](https://cloud.mongodb.com) → **Create a free M0 cluster**
2. Create a **Database User**: Database Access → Add New User
   - Username: `chatbot-user`
   - Password: generate a strong password
   - Role: **Read and write to any database**
3. Whitelist all IPs: Network Access → Add IP Address → `0.0.0.0/0` *(allows Render to connect)*
4. Get connection string: Clusters → Connect → **Drivers**
   ```
   mongodb+srv://chatbot-user:<password>@cluster0.xxxxx.mongodb.net/chatbot_db?retryWrites=true&w=majority
   ```
5. Replace `<password>` with your actual password — this is your `MONGODB_URI`

---

### 2. Backend — Configuration Files

#### a) `backend/render.yaml`
Pre-configured in the repository to automate Render setup:

```yaml
services:
  - type: web
    name: chatbot-api
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: GROQ_API_KEY
        sync: false
      - key: GROQ_MODEL
        value: openai/gpt-oss-120b
      - key: TAVILY_API_KEY
        sync: false
      - key: MONGODB_URI
        sync: false
      - key: MONGODB_DATABASE
        value: chatbot_db
      - key: JWT_SECRET
        sync: false
      - key: JWT_ALGORITHM
        value: HS256
      - key: JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        value: "1440"
      - key: FRONTEND_ORIGIN
        sync: false
      - key: MAX_HISTORY_MESSAGES
        value: "10"
      - key: DOCUMENT_STORAGE_DIR
        value: storage/documents
      - key: VECTOR_STORAGE_DIR
        value: storage/vectors
      - key: MAX_DOCUMENT_SIZE_MB
        value: "15"
```

#### b) `backend/runtime.txt`
```
3.11.9
```

---

### 3. Frontend — Configuration Files

#### `frontend/vercel.json` *(SPA routing — required for client-side routing)*
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

---

## 🖥️ Part 1: Deploy Backend on Render

If your service is **already created** on Render, pushing to GitHub will automatically trigger a new build and deployment. You do **not** need to recreate the service!

### If Creating a New Web Service on Render:
1. Go to [https://render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repository: `vedant-chautiwar/chatbot`
3. Configure settings:

| Setting | Value |
|---|---|
| **Name** | `chatbot-api` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

### Environment Variables on Render
Under **Environment** tab, ensure the following are configured:

| Key | Value / Description | Required? |
|---|---|---|
| `ENVIRONMENT` | `production` | Yes |
| `GROQ_API_KEY` | `gsk_...` (from console.groq.com) | Yes |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Yes |
| `TAVILY_API_KEY` | `tvly-...` (from tavily.com) | Yes |
| `MONGODB_URI` | `mongodb+srv://...` (from Atlas) | Yes |
| `MONGODB_DATABASE` | `chatbot_db` | Yes |
| `JWT_SECRET` | Super secure random string (at least 32 chars) | Yes |
| `JWT_ALGORITHM` | `HS256` | Yes |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Yes |
| `FRONTEND_ORIGIN` | `https://your-frontend.vercel.app` *(update after frontend is live)* | Yes |
| `MAX_HISTORY_MESSAGES` | `10` | Yes |
| `DOCUMENT_STORAGE_DIR` | `storage/documents` *(New in 2.0)* | Optional (defaults to `storage/documents`) |
| `VECTOR_STORAGE_DIR` | `storage/vectors` *(New in 2.0)* | Optional (defaults to `storage/vectors`) |
| `MAX_DOCUMENT_SIZE_MB` | `15` *(New in 2.0)* | Optional (defaults to `15`) |

---

## 🌐 Part 2: Deploy Frontend on Vercel

If already connected to your GitHub repository, Vercel will automatically redeploy on git push.

### If Setting Up Fresh on Vercel:
1. Go to [https://vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import `vedant-chautiwar/chatbot`
3. Configure:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://chatbot-api-xxxx.onrender.com/api` *(replace with your actual Render URL)*

---

## 📦 What New Deployment Steps Are Needed for ChautiBot 2.0?

You **do not need to create new services or databases** on Render or Vercel. 

### What Render Handles Automatically:
1. **New Dependencies**: Render will automatically install the new dependencies from `backend/requirements.txt`:
   - `python-multipart` (handles multipart uploads)
   - `pymupdf` (extracts text from PDF files)
   - `faiss-cpu` (manages vector indexes)
   - `fastembed` (generates local embeddings via `BAAI/bge-small-en-v1.5`)
2. **Directory Creation**: `storage/documents` and `storage/vectors` will be created automatically on the Render container filesystem at startup.

### Important Notes for Render Free Tier:
- **First Upload Latency**: On the first document upload, FastEmbed will download model weights (~50 MB ONNX model). Subsequent chunk embeddings are fast.
- **Ephemeral Storage**: On Render Free tier, container storage is ephemeral. Uploaded files and FAISS vectors exist during the service's lifetime, but if Render spins down the service after 15 minutes of inactivity, files in `storage/` are reset. 
  *(Optional for production)*: If you want persistent file storage on Render, you can attach a Render **Persistent Disk** mounted at `/opt/render/project/src/backend/storage` in Render settings.
- **Resilient Fallback**: If memory constraints occur on Render's 512 MB free tier, ChautiBot's built-in fallback embedder automatically maintains uptime and prevents crashes.

---

## 🚀 Pushing Changes to GitHub

Run these commands in PowerShell or terminal from the project root:

```bash
# 1. Review status of changes
git status

# 2. Stage all modifications and newly created files
git add .

# 3. Commit with a descriptive message
git commit -m "feat: ChautiBot 2.0 with document analysis and code assistant"

# 4. Push to GitHub main branch
git push origin main
```

### What Happens After `git push`:
1. **GitHub** receives the commit on `main`.
2. **Render** detects the new commit on `main` and triggers a build:
   - Installs new pip dependencies (`pymupdf`, `faiss-cpu`, `fastembed`, `python-multipart`).
   - Runs `uvicorn app.main:app` and exposes the new `/api/documents/*` endpoints.
3. **Vercel** detects the new commit on `main` and builds the frontend:
   - Bundles the new Paperclip upload component, document citation cards, and code assistant UI.
   - Deploys live in ~1 minute.

---

## 🩺 Verification After Deployment

### 1. Check Render Backend
Open `https://<your-render-url>/api/health` in your browser.
Expected JSON:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production",
  "components": {
    "api": "ok",
    "database": "ok",
    "tavily_configured": true,
    "groq_configured": true
  }
}
```

### 2. Check Swagger Interactive Docs
Open `https://<your-render-url>/docs` and verify the new document endpoints exist under the **documents** tag:
- `POST /api/documents/upload`
- `GET /api/documents`
- `GET /api/documents/{document_id}`
- `DELETE /api/documents/{document_id}`

### 3. Check Vercel Frontend
1. Open your Vercel URL.
2. Log in or create an account.
3. Verify that the message input has the **Paperclip attachment button**.
4. Test by uploading a PDF, TXT, or code file and asking a question!
