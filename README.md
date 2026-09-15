# The Lenny Growth Assistant 🚀

> **An AI-powered Growth & Product Strategy Assistant built on Lenny's Podcast Transcripts.**  
> Features **RAG retrieval with grounded citations**, **Ship 30 for 30 essay generation (~1,250 words)**, **interactive HTML/CSS artifact generation in a sandboxed viewer**, and **multi-provider LLM toggling (Claude, OpenAI, and local Ollama)**.

---

## 📸 Overview & Key Features

1. **Grounded RAG Q&A**: Answers questions by performing vector search (`pgvector`) across iconic Lenny's Podcast transcripts (Brian Chesky, Shreyas Doshi, Elena Verna, Marty Cagan, Gokul Rajaram). Provides direct source citations (Episode, Guest, Timestamp). Explicitly refuses to guess when context is missing.
2. **Ship 30 for 30 Content Engine**: Generates ~1,250-word essays adhering strictly to Ship 30 for 30 writing principles (strong hook, skimmable subheadings, narrative progression, 1 core actionable takeaway, grounded claims).
3. **Interactive Visual Artifacts**: Generates interactive HTML/CSS diagrams (growth loops, LNO matrices, product checklists) rendered side-by-side in a **sandboxed `<iframe>` Viewer** (`sandbox="allow-scripts"` with zero same-origin or storage access).
4. **Multi-Provider Architecture**: Seamless switching between **Anthropic Claude 3.5 Sonnet**, **OpenAI GPT-4o**, and **Local Ollama** (e.g. `llama3.2` / `qwen2.5:3b`) with automatic fallback.

---

## ⚡ Quickstart (One-Command Startup)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- *(Optional for Local LLM)* [Ollama](https://ollama.com/) running locally on port 11434.

### 1-Step Launch via Docker Compose
```bash
docker-compose up --build
```
Once initialized:
- **Frontend App**: Open [http://localhost:8000](http://localhost:8000)
- **API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Checks**:
  - Main App: `http://localhost:8000/health`
  - Database & pgvector: `http://localhost:8000/health/db`
  - LLM Provider: `http://localhost:8000/health/llm`

---

## 🛠 Local Development Setup (Without Docker)

### 1. Environment Setup
Clone the repository and copy the environment template:
```bash
cp .env.example .env
```

### 2. Install Python Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Database Setup (Local Postgres with pgvector)
Ensure PostgreSQL is running on port 5432 with `pgvector` enabled:
```sql
CREATE DATABASE lenny_growth_db;
\c lenny_growth_db;
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Run Ingestion Script
Ingest and vector-index the Lenny podcast transcripts:
```bash
python ingestion/ingest.py
```

### 5. Start Backend Server
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🦙 Ollama Local Model Setup

To use the mandatory local model demo mode:
1. Install Ollama: [ollama.com](https://ollama.com)
2. Pull a recommended lightweight model:
   ```bash
   ollama pull llama3.2
   # or
   ollama pull qwen2.5:3b
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```
4. Select **Ollama** in the UI top-bar provider toggle or set `DEFAULT_LLM_PROVIDER=ollama` in `.env`.

---

## 🧪 Running Tests

Execute the automated pytest suite covering endpoints, sessions, RAG retrieval, skill formatting, and provider fallbacks:
```bash
pytest -v tests/
```

---

## 📁 Repository Structure

```
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint & router assembly
│   │   ├── config.py         # Settings & environment configuration
│   │   ├── db.py             # Database connection & pgvector setup
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── logging_config.py # Structured logging & transcript recorder
│   │   ├── agent/            # Multi-provider LLM adapter & skill router
│   │   │   ├── provider.py   # Anthropic / OpenAI / Ollama adapter
│   │   │   ├── embeddings.py # Local sentence-transformers / API embeddings
│   │   │   └── skills/       # RAG, Ship 30/30, and Artifact skills
│   │   └── api/              # Endpoint handlers (health, chat, sessions, artifacts)
├── frontend/                 # Glassmorphic Web App UI & Sandboxed Viewer
│   ├── index.html            # Main SPA HTML
│   ├── css/style.css         # Styling system
│   └── js/                   # App logic, API client, sandboxed iframe controller
├── ingestion/                # Transcript dataset & pgvector ingestion CLI
│   ├── data/                 # Raw podcast transcript JSON files
│   └── ingest.py             # Parser & vector index builder
├── agent-transcripts/        # AI development trajectory logs (redacted)
├── tests/                    # Pytest suite
├── PRD.md                    # Product Requirements Document & Discovery Brief
├── design.md                 # Visual design system & security specs
├── architecture.md           # Database ERD, API specs & component flows
├── demo-video-script.md      # 2-3 minute presentation video script
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Backend container configuration
└── .env.example              # Environment variables template
```
