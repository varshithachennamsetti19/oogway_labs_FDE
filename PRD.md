# Product Requirements Document (PRD) & Discovery Brief
## Project: The Lenny Growth Assistant

---

## 1. Discovery Brief

### 1.1 User Persona & Problem Statement
* **Primary User**: Product Managers (PMs), Growth Leaders, Product Marketers, and Startup Founders.
* **Job to be Done (JTBD)**: When building product features, setting growth strategies, or writing internal strategy docs/essays, practitioners need actionable, battle-tested advice from top technology leaders (e.g., Brian Chesky, Shreyas Doshi, Elena Verna, Marty Cagan).
* **Pain Point Removed**: Synthesizing hours of podcast transcripts and newsletter issues into clear, structured, actionable advice is tedious. Existing LLMs often hallucinate generic advice without concrete real-world context or source attribution. "The Lenny Growth Assistant" provides grounded Q&A with direct citations to transcript timestamps/episodes, transforms knowledge into structured Ship 30 for 30 essays, and renders interactive visual artifacts (framing frameworks, growth loops, checklists) in a secure UI.

### 1.2 Success Metrics
1. **Groundedness & Citation Accuracy**: $\ge 95\%$ of RAG answers cite exact source episodes with valid metadata; 0 hallucinated quotes when knowledge is missing (explicit refusal triggered).
2. **Essay Quality & Structure Compliance**: $100\%$ compliance of Ship 30 for 30 essay outputs with the 5-point structure (Hook, Retain, Payoff, ~1,250 words, skimmable formatting, 1 key actionable takeaway).
3. **Artifact Security & Render Latency**: $0$ cross-origin or script execution leaks from sandboxed HTML/CSS artifacts; median viewer rendering latency under 100ms.
4. **Operational Reliability**: Operational health endpoints (`/health`, `/health/db`, `/health/llm`) responding in under 50ms with zero unhandled 500 errors across provider toggles.

### 1.3 Scope & Explicit Choices

| Domain | In Scope | Out of Scope (Justification) |
|---|---|---|
| **Transcripts Data** | High-density subset of iconic Lenny's Podcast transcripts (Chesky, Doshi, Verna, Cagan, Rajaram) with metadata (guest, episode title, URL, topics). | Scraping all 200+ episodes dynamically (Avoids rate-limiting & uncontrolled API dependencies during evaluation). |
| **Authentication** | Session-based state management (UUID-tagged sessions). | Enterprise SSO/OAuth2 (Overhead not required for single-user evaluation; documented extension point). |
| **LLM Providers** | Cloud (Anthropic Claude 3.5 Sonnet / OpenAI GPT-4o) + Local (Ollama with `llama3.2` / `qwen2.5:3b` / `mistral`) with fallback mechanism. | Fine-tuning custom models (Unnecessary latency and cost for RAG + prompt-engineered skills). |
| **Vector Store** | PostgreSQL with `pgvector` extension running in Docker Compose. | Third-party managed vector DBs like Pinecone/Weaviate (Keeps single containerized database stack). |
| **Artifact Security** | Sandboxed `<iframe>` with strict CSP, isolated origin, blocked parent storage/cookie access. | Unrestricted script execution or live API mutation inside artifacts (Eliminates XSS/RCE vectors). |

### 1.5 Key Assumptions
1. **Deployment Environment**: App runs locally via Docker Compose or `uvicorn` on a single host machine with standard modern hardware (8GB+ RAM).
2. **Local Model Availability**: Evaluators can run Ollama locally or rely on automated mock/cloud fallbacks seamlessly.
3. **Single-tenant / Demo Mode**: Session data is stored per session ID in Postgres without multi-tenant workspace isolation.

### 1.6 Risks & Trade-Offs

| Risk / Trade-off | Consequence | Design Mitigation |
|---|---|---|
| **Hallucination in RAG** | Providing incorrect growth advice to PMs. | Strict prompt guardrails requiring explicit citation of transcript chunks; if retrieval score $< \text{threshold}$, agent explicitly states lack of information. |
| **Local Model Quality Ceiling** | Small local models (e.g. 3B parameters) may struggle with long complex essay generation (~1,250 words). | Hybrid skill template system: rigid structural placeholders filled by local model chunks, plus cloud fallback capability. |
| **Unsafe Artifact Rendering (XSS)** | Generated HTML/CSS executing malicious JS or reading app context. | Rendered inside `<iframe sandbox="allow-scripts">` without `allow-same-origin`, with a restrictive Content Security Policy (CSP). |
| **Provider Downtime / API Failure** | App crashing during evaluator demo. | Automatic fallback logic (Cloud $\rightarrow$ Local Ollama $\rightarrow$ Graceful error response with active health status). |

---

## 2. Core User Flows

### Flow 1: Grounded Growth Q&A
1. User enters question (e.g., *"How does Brian Chesky approach product management vs traditional PM roles?"*).
2. Agent Router identifies topic, triggers `rag_skill`.
3. Vector search retrieves top matching transcript chunks from Postgres `pgvector`.
4. Response is rendered with inline transcript citations (Episode Title, Guest, Timestamp/Topic).

### Flow 2: Ship 30 for 30 Essay Generation
1. User requests an essay (e.g., *"Write a Ship 30 for 30 essay on Elena Verna's product-led growth loops"*).
2. Agent Router invokes `ship30_skill`.
3. Skill retrieves relevant Elena Verna transcript insights and enforces Ship 30 for 30 principles (Hook, Retain, Payoff, Skimmable Formatting, 1 Takeaway, ~1,250 words).
4. Full essay rendered in Markdown in the chat.

### Flow 3: Visual Artifact Creation & Preview
1. User requests a framework or visualization (e.g., *"Create an HTML/CSS growth loop diagram for PLG"*).
2. Agent Router invokes `artifact_skill`.
3. Assistant returns message and registers artifact ID.
4. UI opens side-by-side **Artifact Viewer** displaying the sandboxed rendered preview with toggleable raw code view.

---

## 3. Acceptance Criteria

- [x] **Endpoints**: `/health`, `/health/db`, `/health/llm`, `/api/sessions`, `/api/chat`, `/api/artifacts/{id}` implemented cleanly with Pydantic validation.
- [x] **Agent Layer**: Skill router supporting standard RAG Q&A, Ship 30 for 30 essay generator, and HTML/Markdown Artifact creation.
- [x] **RAG**: Transcripts ingested, embedded with `pgvector`, with grounded source citations and explicit non-found handling.
- [x] **Providers**: Configurable via `.env`, supporting Anthropic Claude, OpenAI, and local Ollama models with transparent status surfacing.
- [x] **Frontend UI**: Responsive dual-pane view with session management, streaming/thinking indicators, inline citations, model indicator, and sandboxed Artifact Viewer.
- [x] **Deliverables**: Complete documentation (`PRD.md`, `design.md`, `architecture.md`, `README.md`, `demo-video-script.md`), Docker Compose, test suite, and redacted development transcripts.
