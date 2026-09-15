# Demo Video Script & Walkthrough Outline
## Project: The Lenny Growth Assistant
**Target Duration**: 2–3 minutes  
**Format**: Camera-on screen recording + narration

---

## 🎬 Act 1: Problem Statement & Value Proposition (0:00 – 0:35)

- **Visual**: Camera on speaker, then transition to "The Lenny Growth Assistant" homepage interface.
- **Talking Points**:
  > *"Hi everyone! Product Managers and Growth leaders spend hours sifting through podcasts and newsletters looking for actionable frameworks. But generic AI assistants often hallucinate advice without real-world context or source attribution.*
  >
  > *Meet **The Lenny Growth Assistant** — a full-stack, AI-powered assistant built on transcripts from top tech leaders like Brian Chesky, Shreyas Doshi, and Elena Verna. It delivers grounded Q&A with direct source citations, transforms ideas into structured Ship 30 for 30 essays (~1,250 words), and generates interactive visual artifacts inside a securely sandboxed viewer."*

---

## 🚀 Act 2: Live Product Walkthrough & Grounded RAG (0:35 – 1:20)

- **Visual**: Demoing Grounded Q&A in the chat interface.
- **Action**: Type: *"What is Shreyas Doshi's LNO framework and how should a PM apply it?"*
- **Talking Points**:
  > *"First, let's ask about Shreyas Doshi's LNO framework. Notice the live agent thinking state as it queries our PostgreSQL `pgvector` database.*
  >
  > *The assistant returns a detailed response with **inline transcript citations**. If I click this citation pill, I can see the exact episode title, guest name, and context match. And if I ask about something completely outside our knowledge base, the assistant explicitly states it cannot find relevant transcript evidence rather than hallucinating generic answers."*

---

## ✍️ Act 3: Ship 30 for 30 Skill & Sandboxed Artifact Viewer (1:20 – 2:10)

- **Visual**: Requesting a Ship 30 for 30 essay and opening an interactive HTML artifact.
- **Action**:
  1. Type: *"Write a Ship 30 for 30 essay on Elena Verna's product-led growth loops."*
  2. Scroll through the generated essay.
  3. Type: *"Create an interactive HTML framework for the LNO Matrix."*
  4. Click the Artifact Card to open the side-by-side Sandboxed Viewer.
- **Talking Points**:
  > *"Next, let's invoke our **Ship 30 for 30 Essay Skill**. The assistant formats a comprehensive ~1,250-word essay adhering to the 5 Ship 30 for 30 principles: a magnetic hook, skimmable subheadings, narrative progression, 1 core takeaway, and grounded citations.*
  >
  > *Now, watch what happens when I ask for a visual artifact. The assistant generates clean HTML/CSS code and opens our **Artifact Viewer**. Under the hood, this renders inside a strictly sandboxed iframe (`sandbox="allow-scripts"`) with no same-origin or storage access — preventing any XSS or credential leakage while giving users an interactive visual experience."*

---

## 🦙 Act 4: Local Ollama Demo & Technical Trade-offs (2:10 – 3:00)

- **Visual**: Switching the provider badge to **Ollama (Llama 3.2)** and demonstrating a query.
- **Action**: Click model dropdown $\rightarrow$ Select `Ollama (Llama 3.2)` $\rightarrow$ Submit prompt $\rightarrow$ Show `/health/llm` JSON.
- **Talking Points**:
  > *"Finally, operational readiness and local LLM execution. In the top bar, I can toggle between Anthropic Claude 3.5 Sonnet, OpenAI, and a completely local model running via **Ollama**.*
  >
  > *Here, with Ollama active, the assistant runs 100% locally on a standard laptop. If Ollama becomes unresponsive, our fallback adapter seamlessly degrades or alerts the user without unhandled 500 errors.*
  >
  > *One key technical trade-off we made was using PostgreSQL with `pgvector` rather than a third-party vector store. This reduced operational complexity to a single containerized database while maintaining sub-50ms vector query performance.*
  >
  > *Everything is containerized in a single `docker-compose up` command. Thanks for watching!"*
