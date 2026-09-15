# Manual UI & Security Test Plan (`manual-ui-test-plan.md`)
## Project: The Lenny Growth Assistant

This document provides a concise step-by-step checklist for manually testing and evaluating **The Lenny Growth Assistant** user interface, RAG retrieval, Ship 30 for 30 essay generation, and Sandboxed Artifact Viewer security.

---

## 📋 Test Suite Checklist

### 1. Operational Readiness & Health Checks
- [ ] **Step 1.1**: Open `http://localhost:8000/health` in browser.
  - **Expected**: JSON response `{"status": "ok", "version": "1.0.0"}`.
- [ ] **Step 1.2**: Open `http://localhost:8000/health/db`.
  - **Expected**: `{"status": "ok", "database": "postgresql", "pgvector_enabled": true}`.
- [ ] **Step 1.3**: Open `http://localhost:8000/health/llm`.
  - **Expected**: `{"status": "ok", "active_provider": "anthropic" | "ollama", ...}`.

---

### 2. Session Management & Isolation
- [ ] **Step 2.1**: Click **"+ New Growth Session"** in the sidebar.
  - **Expected**: A new session tab appears with initial welcome message.
- [ ] **Step 2.2**: Send message *"What did Shreyas Doshi say about LNO?"* in Session A.
  - **Expected**: Response with citations renders in Session A.
- [ ] **Step 2.3**: Click **"+ New Growth Session"** again to start Session B. Send message *"What is Brian Chesky's product philosophy?"*.
  - **Expected**: Session B renders only Brian Chesky advice.
- [ ] **Step 2.4**: Switch back to Session A in the sidebar.
  - **Expected**: Session A retains its previous context and messages without leaking Session B data.
- [ ] **Step 2.5**: Test Conversational Memory Recall & Isolation:
  - Tell Session A: *"My secret project name is Varshitha."*
  - Ask Session A: *"What is my secret project name?"* $\rightarrow$ Assistant recalls *"Varshitha"*.
  - Create Session B and ask *"What is my secret project name?"* $\rightarrow$ Assistant replies *"I don't have that information in this conversation."*.
  - Return to Session A and ask again $\rightarrow$ Assistant retains and recalls *"Varshitha"*.

---

### 3. Grounded RAG Retrieval & Source Citations
- [ ] **Step 3.1**: Ask *"What is Shreyas Doshi's LNO framework?"*.
  - **Expected**:
    1. Animated agent thinking state appears (*"Searching vector index..."*).
    2. Response details Leverage, Neutral, and Overhead tasks.
    3. Interactive **Citation Pills** appear below the response showing `Shreyas Doshi (06:10)`.
- [ ] **Step 3.2**: Ask an out-of-scope question: *"How do I bake a French baguette?"*.
  - **Expected**: Assistant explicitly states: *"I couldn't find any relevant transcript evidence... To prevent hallucination, I only answer based on grounded transcript records."*

---

### 4. Ship 30 for 30 Content Skill
- [ ] **Step 4.1**: Click the shortcut chip or type *"Write a Ship 30 for 30 essay on Elena Verna's product-led growth loops"*.
  - **Expected**:
    1. Agent routes to `ship30_skill`.
    2. Outputs a structured ~1,250 word essay.
    3. Contains strong bold hook, short paragraphs, skimmable Markdown headers (`##`), bullet points, and 1 actionable takeaway at the end.

---

### 5. Interactive Artifact Generation & Sandboxed Viewer Security
- [ ] **Step 5.1**: Ask *"Create an interactive HTML framework matrix for the LNO framework"*.
  - **Expected**:
    1. Assistant response includes an **Artifact Card**: `🎨 Artifact: Create an interactive HTML framework...`.
    2. Side-by-side **Sandboxed Artifact Viewer** slides open.
- [ ] **Step 5.2**: Test Viewer Tabs (**Preview** vs **Code Source**).
  - **Expected**: Switching to "Code Source" displays the raw HTML/CSS code; switching to "Preview" renders the interactive card inside an iframe.
- [ ] **Step 5.3**: Security Verification (XSS & Storage Isolation):
  - Inspect the iframe tag in browser DevTools.
  - **Expected**: `sandbox="allow-scripts"` without `allow-same-origin`. The iframe cannot access parent window's `localStorage`, `sessionStorage`, or cookies.

---

### 6. Provider Toggle (Cloud <-> Ollama Local Model)
- [ ] **Step 6.1**: Change top-bar dropdown to **"Ollama (Local Llama 3.2)"**.
  - **Expected**: Provider badge updates to `Online (ollama)`.
- [ ] **Step 6.2**: Submit a new prompt.
  - **Expected**: Message processed locally via Ollama HTTP endpoint or offline fallback with zero application crashes.
