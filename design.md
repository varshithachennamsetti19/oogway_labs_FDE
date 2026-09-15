# Design Specification (`design.md`)
## Project: The Lenny Growth Assistant

---

## 1. Design Philosophy & System Objectives

The Lenny Growth Assistant interface is designed for Product Managers, Growth Practitioners, and Tech Leaders who need fast, grounded, highly structured insights. The visual aesthetics leverage modern glassmorphism, crisp typography (Inter/Outfit style), rich dark mode palette, dynamic micro-interactions, and clear visual hierarchy.

---

## 2. Information Architecture & Layout

The user interface follows a **Responsive Dual-Pane Architecture**:

```
+-----------------------------------------------------------------------------------------+
|                                    TOP BAR / HEADER                                      |
|  [Logo: Lenny Growth Assistant]  [Active Model: Claude / Ollama / OpenAI]  [Health: OK]   |
+------------------------------------+----------------------------------------------------+
|            SIDEBAR                 |                 MAIN CHAT STREAM                   |
|                                    |                                                    |
|  [+ New Chat Session]              |  [Assistant]: Welcome! How can I help you scale    |
|                                    |               your product today?                  |
|  Recent Sessions:                  |                                                    |
|  - PLG Loops with Elena Verna      |  [User]: What is Shreyas Doshi's LNO framework?    |
|  - Brian Chesky PM Philosophy      |                                                    |
|  - Ship 30/30 Essay on Growth      |  [Assistant Thinking... RAG Searching]             |
|                                    |                                                    |
|  System Status:                    |  [Assistant]: Shreyas Doshi divides tasks into...  |
|  - DB: Connected (pgvector)        |   [Citation 1: Shreyas Doshi Episode]              |
|  - Ollama: Ready                   |                                                    |
|                                    |  +----------------------------------------------+  |
|                                    |  | [Artifact Generated: LNO Matrix Interactive]  |  |
|                                    |  | Click to open in Artifact Viewer ->           |  |
|                                    |  +----------------------------------------------+  |
|                                    |                                                    |
|                                    |  [ Input Box: Ask a question, request an essay... ]|
+------------------------------------+----------------------------------------------------+
|                                ARTIFACT VIEWER SLIDE-OVER                               |
|                     (Sandboxed <iframe> | Raw HTML/CSS Code Toggle)                     |
+-----------------------------------------------------------------------------------------+
```

### Key UI Components
1. **Top Bar**: Displays system identity, active LLM provider toggle badge (Anthropic / OpenAI / Ollama), and real-time backend health diagnostic pill (`/health`).
2. **Session Drawer (Sidebar)**: Supports switching between chat sessions, initializing new chat sessions, and monitoring DB/LLM connection states.
3. **Chat Stream**:
   - Distinct user vs assistant message bubbles with smooth animations.
   - Live "Thinking & Retrieving" indicators showing active agent tool execution (e.g. *Searching vector store...*, *Synthesizing Ship 30 for 30 Essay...*).
   - Grounded citations rendered as interactive metadata pills showing episode title, guest name, and context match confidence.
   - Clickable **Artifact Cards** that trigger the slide-out Artifact Viewer.
4. **Artifact Viewer Panel**:
   - Renders side-by-side or as a full overlay.
   - Features dual tabs: **Preview (Sandboxed HTML/CSS)** and **Code (Syntax Highlighted Source)**.
   - Interactive zoom/refresh and copy-to-clipboard buttons.

---

## 3. Visual Styling & Design Tokens

- **Color Palette**:
  - Background: Deep Slate `#0B0F19` with subtle radial gradients (`#111827`).
  - Container / Cards: Translucent dark glass (`rgba(30, 41, 59, 0.7)`), `backdrop-filter: blur(16px)` with thin borders (`1px solid rgba(255, 255, 255, 0.08)`).
  - Accent / Primary: Electric Indigo (`#6366F1`) & Purple Glow (`#8B5CF6`).
  - Text Primary: Neutral Snow (`#F9FAFB`), Text Secondary: Muted Gray (`#9CA3AF`).
  - Citation Pills: Soft Teal (`#0D9488` background with `#5EEAD4` text).
  - Success / Health Badge: Emerald (`#10B981`).
  - Warning / Local Model Badge: Amber (`#F59E0B`).

- **Typography**:
  - Primary Font: `Inter`, system-ui, `-apple-system`, `sans-serif`.
  - Monospace Font (Code & Citations): `JetBrains Mono`, `Fira Code`, `monospace`.

---

## 4. Key Interaction States

1. **Empty State**: Displays quick prompt templates (e.g., *"Explain Brian Chesky's product philosophy"*, *"Write a Ship 30 for 30 essay on Elena Verna PLG"*, *"Create an interactive HTML framework for LNO"*).
2. **Loading / Streaming State**: Animated pulse indicator with step summary (*"Querying pgvector index..."*).
3. **Error State**: Non-intrusive toast notification + retry pill when Ollama or API key is unavailable (no unhandled page crashes).
4. **Artifact Preview State**: Smooth slide-in drawer rendering the sandbox iframe with zero lag.

---

## 5. Security Architecture for Artifacts

Treating generated HTML/CSS artifacts as **untrusted user content**:

- **Iframe Isolation**:
  ```html
  <iframe
    id="artifact-frame"
    sandbox="allow-scripts"
    csp="default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'unsafe-inline';"
    srcdoc="..."
  ></iframe>
  ```
- **Security Protections Enforced**:
  - `allow-same-origin` is **EXPLICITLY REMOVED** to prevent the artifact iframe from accessing parent window cookies, `localStorage`, `sessionStorage`, or DOM elements.
  - Strict Content Security Policy (CSP) blocks outbound network calls from inside the artifact (`default-src 'none'`).
  - No access to main app API endpoints or auth headers.

---

## 6. Accessibility & Responsiveness

- **Keyboard Navigation**: Full `Tab` focus support, `Esc` key closes Artifact Viewer.
- **ARIA Standards**: `aria-live="polite"` on chat stream for screen reader announcements; proper `role="region"` for drawer panels.
- **Responsive Layout**: Collapses to single-column view on viewports $< 768\text{px}$ with a floating drawer button for artifact viewing.
