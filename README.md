# The Lenny Growth Assistant ⚡

> **An AI-Powered Growth & Product Strategy Assistant Grounded on Lenny's Podcast Transcripts**  
> Features **RAG retrieval with grounded citations**, **Ship 30 for 30 essay generation (~1,250 words)**, **interactive HTML visual artifact generation in a sandboxed viewer**, **multi-provider LLM toggling (Claude 3.5 Sonnet, OpenAI GPT-4o, Local Ollama)**, and a **pitch-black & electric navy blue visual theme**.

---

## 📖 Project Overview & Brief Explanation

**The Lenny Growth Assistant** is a specialized AI strategy partner built for Product Managers, Growth Leaders, and Tech Founders. Instead of generic or hallucinated advice, the assistant retrieves battle-tested frameworks directly from iconic interviews on **Lenny's Podcast** (featuring Brian Chesky, Shreyas Doshi, Elena Verna, Marty Cagan, and Gokul Rajaram).

### Key Features
1. **Grounded RAG Q&A**: Performs cosine vector similarity search (`pgvector`) across indexed transcript chunks. Provides direct source citations (Episode Title, Guest, Timestamp). Explicitly refuses to guess when knowledge is absent.
2. **Ship 30 for 30 Content Engine**: Generates ~1,250-word strategy essays following strict Ship 30 for 30 principles (Hook, Retain, Payoff, skimmable subheadings, 1 actionable takeaway).
3. **Interactive Visual Artifacts**: Generates responsive HTML/CSS diagrams (growth loop visualizers, LNO framework matrices, product checklists) rendered side-by-side in a **sandboxed `<iframe>` Viewer** (`sandbox="allow-scripts"` with zero same-origin or storage access).
4. **Multi-Provider LLM Architecture**: Switch seamlessly between **Anthropic Claude 3.5 Sonnet**, **OpenAI GPT-4o**, and **Local Ollama (`llama3.2`)** with automatic fallback.
5. **Pitch-Black & Electric Navy UI**: Styled with a pitch-black background (`#000000`), high-contrast white text (`#FFFFFF`), glowing electric navy blue response boundaries (`#2563EB`), and a custom **VC Monogram Logo**.

---

## 📋 System Requirements & Prerequisites

### Minimum System Requirements
- **OS**: Windows (WSL2 / Docker Desktop), macOS, or Linux
- **RAM**: 8 GB minimum (16 GB recommended if running local LLMs via Ollama)
- **Disk Space**: ~2 GB free disk space

### Prerequisites
- **[Docker & Docker Compose](https://docs.docker.com/get-docker/)** (Recommended for 1-step startup)
- **[Python 3.10+](https://www.python.org/)** (Required only for local non-Docker development)
- **[PostgreSQL 16 with pgvector extension](https://github.com/pgvector/pgvector)** (Included automatically in Docker Compose)
- **[Ollama](https://ollama.com/)** *(Optional for local LLM execution)*

---

## ⚡ Quickstart Guide (What to Do)

### Option 1: 1-Step Docker Launch (Recommended)

1. **Clone the Repository & Navigate to Project Root**:
   ```bash
   git clone <repo-url>
   cd oogway_project
   ```

2. **Configure Environment Variables** *(Optional)*:
   ```bash
   cp .env.example .env
   ```
   *(Add your `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` if using cloud providers. Ollama local mode works out-of-the-box).*

3. **Start the Application Stack**:
   ```bash
   docker-compose up --build
   ```

4. **Access the Application**:
   - 🌐 **Web App Interface**: [http://localhost:8000](http://localhost:8000)
   - 📚 **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - 🩺 **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Option 2: Manual Local Development Setup (Without Docker)

1. **Set Up Python Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # macOS / Linux:
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start PostgreSQL with `pgvector`**:
   Ensure PostgreSQL 16 is running on port 5432 with `pgvector` installed:
   ```sql
   CREATE DATABASE lenny_growth_db;
   \c lenny_growth_db;
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

4. **Ingest & Vector-Index Transcripts**:
   ```bash
   python ingestion/ingest.py
   ```

5. **Start FastAPI Backend Server**:
   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 🦙 Ollama Local LLM Setup

To run the assistant 100% locally with zero external API calls:

1. Download and install Ollama from [ollama.com](https://ollama.com).
2. Pull the recommended local model:
   ```bash
   ollama pull llama3.2
   ```
3. Start the Ollama daemon:
   ```bash
   ollama serve
   ```
4. Select **Ollama (Local Llama 3.2)** in the top-right header provider dropdown in the UI.

---

## ⚙️ Environment Variables Reference (`.env`)

| Variable | Default Value | Description |
|---|---|---|
| `PROJECT_NAME` | `The Lenny Growth Assistant` | Application display name |
| `DEFAULT_LLM_PROVIDER` | `anthropic` | Active LLM provider (`anthropic`, `openai`, or `ollama`) |
| `ANTHROPIC_API_KEY` | `""` | Anthropic API key for Claude 3.5 Sonnet |
| `OPENAI_API_KEY` | `""` | OpenAI API key for GPT-4o |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama local endpoint URL |
| `OLLAMA_MODEL` | `llama3.2` | Local model name in Ollama |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string with pgvector |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers embedding model (384d) |

---

## 🧪 Running Automated Tests

Run the complete 18-test automated pytest suite:
```bash
pytest -v tests/
```

Test Coverage Includes:
- System Health Endpoints (`/health`, `/health/db`, `/health/llm`)
- Multi-Provider LLM Fallback Logic
- Vector Search & Citation Retrieval
- Session Memory & State Isolation
- Security Sandbox & CSP Policies
- Essay & Artifact Skill Tool Call Routers

---

## 📐 Project Architecture & Requirements Compliance

### Dataset Specification
- **Curated Dataset**: High-density transcripts from 5 iconic tech leaders (Brian Chesky, Shreyas Doshi, Elena Verna, Marty Cagan, Gokul Rajaram).
- **Vector Storage**: 60 indexed chunks with 384-dimensional normalized vector embeddings (`all-MiniLM-L6-v2`) in PostgreSQL `pgvector`.
- **RAG Retrieval**: Top-K = 4 similarity search with a strict similarity threshold (`0.25`).

### Security Architecture
- **Sandboxed Artifact Viewer**: Rendered inside `<iframe sandbox="allow-scripts">` without `allow-same-origin` or access to cookies/localStorage.
- **Session Isolation**: Every chat session maintains independent conversation history tagged by UUID with zero cross-session leakage.

---

## 📁 Repository Directory Structure

```
├── backend/                  # FastAPI Application & AI Agent Engine
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint, router assembly, static mounting
│   │   ├── config.py         # Application settings & pydantic environment parsing
│   │   ├── db.py             # Database session manager & pgvector initialization
│   │   ├── models.py         # SQLAlchemy models (TranscriptChunk, Session, Message, Artifact)
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── logging_config.py # Structured logging setup
│   │   ├── agent/            # AI Agent Tool-Calling Layer
│   │   │   ├── router.py     # Tool router & execution pipeline
│   │   │   ├── provider.py   # Multi-provider LLM adapter (Anthropic / OpenAI / Ollama)
│   │   │   ├── embeddings.py # Sentence-transformers embedding generator (384d)
│   │   │   └── skills/       # Agent skills (RAG Q&A, Ship 30/30, Artifacts)
│   │   └── api/              # API Endpoint Routes (health, chat, sessions, artifacts)
├── frontend/                 # Pitch-Black & Navy Blue Web Interface
│   ├── index.html            # Main Single-Page Application HTML
│   ├── css/style.css         # Design system tokens, pitch-black dark theme & glow styles
│   └── js/                   # App controller, API client, sandboxed viewer logic
├── ingestion/                # Transcript Dataset & Vector Indexer
│   ├── data/                 # Raw transcript JSON files (5 curated guests)
│   └── ingest.py             # Ingestion CLI & vector embedding generator
├── tests/                    # Pytest Automated Test Suite (18 unit & integration tests)
├── PRD.md                    # Product Requirements Document & Discovery Brief
├── design.md                 # Design System Tokens & Security Specifications
├── architecture.md           # Architecture Diagrams, Data ERD, API Specifications
├── demo-video-script.md      # 2-3 Minute Presentation Video Script
├── docker-compose.yml        # Docker Compose configuration (Postgres + Backend)
├── Dockerfile                # Backend container build specification
└── .env.example              # Environment variables template
```

---

## 📄 License

This repository is built for educational and research purposes. All transcript content belongs to [Lenny's Podcast](https://www.youtube.com/@LennysPodcast) and the respective guests.
