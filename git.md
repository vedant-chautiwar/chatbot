# 🚀 Git Push Instructions — `chatbot`

Push this project to **github.com/vedant-chautiwar/chatbot**.

---

## 1. Create the GitHub Repository

1. Go to https://github.com/new
2. Set **Repository name** → `chatbot`
3. Leave it **Public** or **Private** (your choice)
4. ❌ Do **NOT** initialize with a README, .gitignore, or license (the project already has these)
5. Click **Create repository**

---

## 2. Initialize & Push (First Time)

Run these commands from the project root (`d:\vedant-coding\chatbot`):

```bash
# Navigate to project root
cd d:\vedant-coding\chatbot

# Initialize git (skip if already initialized)
git init

# Stage all files
git add .

# Create the first commit
git commit -m "Initial commit"

# Rename branch to main (if not already)
git branch -M main

# Add the remote origin
git remote add origin https://github.com/vedant-chautiwar/chatbot.git

# Push to GitHub
git push -u origin main
```

---

## 3. Subsequent Pushes

After the initial push, use:

```bash
git add .
git commit -m "your commit message"
git push
```

---

## 4. Verify the Remote

```bash
# Check remote is set correctly
git remote -v
```

Expected output:
```
origin  https://github.com/vedant-chautiwar/chatbot.git (fetch)
origin  https://github.com/vedant-chautiwar/chatbot.git (push)
```

---

## ⚠️ Important — Files Already Excluded

The `.gitignore` in this project already excludes sensitive files. Double-check these are **never committed**:

| File | Reason |
|------|--------|
| `.env` | Contains API keys (Groq, Tavily, JWT secret) |
| `.venv/` | Python virtual environment |
| `node_modules/` | Frontend dependencies |
| `__pycache__/` | Python bytecode |
| `.pytest_cache/` | Test cache |

> **Tip:** Run `git status` before committing to confirm no `.env` or secrets are staged.

---

## 🔑 Authentication

If prompted for credentials, use a **Personal Access Token (PAT)** instead of your password:

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Select scope: `repo`
4. Copy the token and use it as your password when `git push` prompts you

To avoid re-entering credentials every time:

```bash
git config --global credential.helper manager
```

---

## 🔄 If Remote Already Exists

```bash
# Remove old remote and re-add
git remote remove origin
git remote add origin https://github.com/vedant-chautiwar/chatbot.git
git push -u origin main
```
