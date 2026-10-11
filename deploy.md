# 🚀 Deployment Guide — Chatbot

| Layer        | Platform                                   | URL (after deploy)                      |
| ------------ | ------------------------------------------ | --------------------------------------- |
| **Backend**  | [Render](https://render.com)               | `https://chatbot-api-xxxx.onrender.com` |
| **Frontend** | [Vercel](https://vercel.com)               | `https://chatbot-xxxx.vercel.app`       |
| **Database** | [MongoDB Atlas](https://cloud.mongodb.com) | Cloud-hosted                            |

---

## ✅ Pre-Deployment Checklist

Complete these steps **before** touching Render or Vercel.

### 1. MongoDB Atlas (Free Tier)

You must switch from `localhost` to a cloud database.

1. Go to [https://cloud.mongodb.com](https://cloud.mongodb.com) → **Create a free M0 cluster**
2. Create a **Database User**: Database Access → Add New User
   - Username: `chatbot-user`
   - Password: generate a strong one (save it)
   - Role: **Read and write to any database**
3. Whitelist all IPs: Network Access → Add IP Address → `0.0.0.0/0` _(allows Render)_
4. Get connection string: Clusters → Connect → **Drivers**
   ```
   mongodb+srv://chatbot-user:<password>@cluster0.xxxxx.mongodb.net/chatbot_db?retryWrites=true&w=majority
   ```
5. Replace `<password>` with your actual password — this is your `MONGODB_URI`

---

### 2. Backend — Files to Add

#### a) `backend/render.yaml` _(optional but recommended)_

Create this file to auto-configure Render:

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
```

#### b) `backend/runtime.txt` _(tells Render which Python version)_

```
3.11.9
```

---

### 3. Frontend — Files to Add

#### a) `frontend/vercel.json` _(handles SPA routing — required)_

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

> Without this, refreshing any page (e.g. `/chat`) returns a 404 on Vercel.

---

## 🖥️ Part 1: Deploy Backend on Render

### Step 1 — Create Web Service

1. Go to [https://render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub account → select **vedant-chautiwar/chatbot**
3. Configure:

| Setting            | Value                                              |
| ------------------ | -------------------------------------------------- |
| **Name**           | `chatbot-api`                                      |
| **Root Directory** | `backend`                                          |
| **Runtime**        | `Python 3`                                         |
| **Build Command**  | `pip install -r requirements.txt`                  |
| **Start Command**  | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type**  | `Free`                                             |

### Step 2 — Add Environment Variables

In Render → your service → **Environment** tab, add all of these:

| Key                               | Value                                                                                             |
| --------------------------------- | ------------------------------------------------------------------------------------------------- |
| `ENVIRONMENT`                     | `production`                                                                                      |
| `GROQ_API_KEY`                    | `your-groq-api-key` _(from your .env)_                                                            |
| `GROQ_MODEL`                      | `openai/gpt-oss-120b`                                                                             |
| `TAVILY_API_KEY`                  | `your-tavily-api-key` _(from your .env)_                                                          |
| `MONGODB_URI`                     | `mongodb+srv://chatbot-user:<pw>@cluster0.xxx.mongodb.net/chatbot_db?retryWrites=true&w=majority` |
| `MONGODB_DATABASE`                | `chatbot_db`                                                                                      |
| `JWT_SECRET`                      | `your-jwt-secret` _(from your .env — keep this private)_                                          |
| `JWT_ALGORITHM`                   | `HS256`                                                                                           |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`                                                                                            |
| `FRONTEND_ORIGIN`                 | `https://your-frontend.vercel.app` _(update after Vercel deploy)_                                 |
| `MAX_HISTORY_MESSAGES`            | `10`                                                                                              |

### Step 3 — Deploy & Verify

1. Click **Deploy Web Service** — first deploy takes ~3-5 minutes
2. Once live, open: `https://chatbot-api-xxxx.onrender.com/`
   - Expected response: `{"service":"Agentic AI Chatbot Backend","status":"online",...}`
3. Copy the full Render URL — you will need it for Vercel

> ⚠️ **Free tier note**: Render free services spin down after 15 minutes of inactivity.  
> First request after idle takes ~30 seconds to cold-start.

---

## 🌐 Part 2: Deploy Frontend on Vercel

### Step 1 — Import Project

1. Go to [https://vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import from GitHub → select **vedant-chautiwar/chatbot**
3. Configure:

| Setting              | Value           |
| -------------------- | --------------- |
| **Framework Preset** | `Vite`          |
| **Root Directory**   | `frontend`      |
| **Build Command**    | `npm run build` |
| **Output Directory** | `dist`          |
| **Install Command**  | `npm install`   |

### Step 2 — Add Environment Variables

In the **Environment Variables** section on Vercel, add:

| Key                 | Value                                       |
| ------------------- | ------------------------------------------- |
| `VITE_API_BASE_URL` | `https://chatbot-api-xxxx.onrender.com/api` |

> ⚠️ Replace `chatbot-api-xxxx` with your actual Render service URL from Part 1.  
> The `/api` suffix is required — all backend routes are prefixed with `/api`.

### Step 3 — Deploy & Verify

1. Click **Deploy** — takes ~1-2 minutes
2. Open your Vercel URL → login → send a message
3. If you see the chat working, deployment is complete ✅

---

## 🔁 After Both Are Deployed — Update CORS

Once you have both URLs, go back to **Render → Environment** and update:

```
FRONTEND_ORIGIN = https://your-actual-frontend.vercel.app
```

Then click **Manual Deploy** on Render to apply the change.

---

## 🔄 Redeploying After Code Changes

```bash
# Just push to GitHub — both services auto-deploy on push to main
git add .
git commit -m "your changes"
git push
```

Render and Vercel are both connected to `origin/main` and will automatically redeploy.

---

## 🩺 Health Check URLs

| Endpoint                              | Expected               |
| ------------------------------------- | ---------------------- |
| `GET https://<render-url>/`           | `{"status":"online"}`  |
| `GET https://<render-url>/api/health` | `{"status":"healthy"}` |
| `https://<vercel-url>/`               | Login page loads       |

---

## 🐛 Common Issues

| Problem                         | Fix                                                           |
| ------------------------------- | ------------------------------------------------------------- |
| CORS error in browser           | Update `FRONTEND_ORIGIN` on Render with exact Vercel URL      |
| 404 on page refresh             | Ensure `vercel.json` exists in `frontend/`                    |
| MongoDB connection timeout      | Whitelist `0.0.0.0/0` in Atlas Network Access                 |
| Render cold start delay         | Expected on free tier — upgrade to Starter ($7/mo) to avoid   |
| `VITE_API_BASE_URL` not working | Must prefix with `VITE_` or Vite will ignore it at build time |
| 500 on `/api/chat`              | Check Render logs → likely a missing env var                  |
