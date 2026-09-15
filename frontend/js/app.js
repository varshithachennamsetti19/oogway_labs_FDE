/**
 * Main Application Orchestrator
 */

import * as api from "./api.js";
import { ArtifactViewer } from "./viewer.js";

class App {
  constructor() {
    this.currentSessionId = null;
    this.viewer = new ArtifactViewer();

    this.chatStreamElem = document.getElementById("chat-stream");
    this.chatInputElem = document.getElementById("chat-input");
    this.btnSendElem = document.getElementById("btn-send");
    this.btnNewChatElem = document.getElementById("btn-new-chat");
    this.sessionListElem = document.getElementById("session-list");
    this.providerSelectElem = document.getElementById("provider-select");
    this.healthBadgeElem = document.getElementById("health-badge");
    this.healthTextElem = document.getElementById("health-text");

    this.initEvents();
    this.bootstrap();
  }

  initEvents() {
    this.btnSendElem.addEventListener("click", () => this.handleSendMessage());
    this.chatInputElem.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this.handleSendMessage();
    });

    this.btnNewChatElem.addEventListener("click", () => this.handleCreateSession());

    // Prompt Shortcut Chips
    document.querySelectorAll(".shortcut-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const promptText = chip.getAttribute("data-prompt");
        if (promptText) {
          this.chatInputElem.value = promptText;
          this.handleSendMessage();
        }
      });
    });
  }

  async bootstrap() {
    await this.updateHealthStatus();
    await this.loadSessions();

    if (!this.currentSessionId) {
      await this.handleCreateSession();
    }

    // Health check polling every 15 seconds
    setInterval(() => this.updateHealthStatus(), 15000);
  }

  async updateHealthStatus() {
    const health = await api.checkHealth();
    if (health.status === "ok" || health.active_provider) {
      this.healthBadgeElem.style.background = "rgba(16, 185, 129, 0.1)";
      this.healthBadgeElem.style.color = "var(--success)";
      this.healthTextElem.textContent = `Online (${health.active_provider})`;
    } else {
      this.healthBadgeElem.style.background = "rgba(239, 68, 68, 0.1)";
      this.healthBadgeElem.style.color = "var(--danger)";
      this.healthTextElem.textContent = "Offline Mode";
    }
  }

  async loadSessions() {
    try {
      const sessions = await api.getSessions();
      this.renderSessionList(sessions);
      if (sessions.length > 0 && !this.currentSessionId) {
        await this.selectSession(sessions[0].id);
      }
    } catch (e) {
      console.error("Failed to load sessions:", e);
    }
  }

  renderSessionList(sessions) {
    this.sessionListElem.innerHTML = "";
    sessions.forEach(s => {
      const item = document.createElement("div");
      item.className = `session-item ${s.id === this.currentSessionId ? "active" : ""}`;
      item.innerHTML = `
        <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 180px;">${this.escapeHtml(s.title)}</span>
        <span style="font-size: 0.7rem; color: var(--text-subtle);">${s.message_count || 0}</span>
      `;
      item.addEventListener("click", () => this.selectSession(s.id));
      this.sessionListElem.appendChild(item);
    });
  }

  async handleCreateSession() {
    try {
      const session = await api.createSession("New Growth Session");
      this.currentSessionId = session.id;
      await this.loadSessions();
      this.clearChatStream();
      this.appendWelcomeMessage();
    } catch (e) {
      console.error("Error creating session:", e);
    }
  }

  async selectSession(sessionId) {
    this.currentSessionId = sessionId;
    this.updateActiveSessionUI();
    try {
      const details = await api.getSessionMessages(sessionId);
      this.clearChatStream();
      if (details.messages.length === 0) {
        this.appendWelcomeMessage();
      } else {
        details.messages.forEach(msg => {
          this.appendMessageUI(msg.role, msg.content, msg.citations, msg.artifacts);
        });
      }
    } catch (e) {
      console.error("Failed to load session messages:", e);
    }
  }

  updateActiveSessionUI() {
    document.querySelectorAll(".session-item").forEach(el => {
      el.classList.remove("active");
    });
    this.loadSessions();
  }

  clearChatStream() {
    this.chatStreamElem.innerHTML = "";
  }

  appendWelcomeMessage() {
    const welcomeHTML = `
      Welcome to **The Lenny Growth Assistant**!\n\n
      I provide grounded strategy advice from top technology leaders (*Brian Chesky, Shreyas Doshi, Elena Verna, Marty Cagan, Gokul Rajaram*).\n\n
      Try asking a grounded question, requesting a **Ship 30 for 30 essay (~1,250 words)**, or asking for an **interactive visual HTML artifact**.
    `;
    this.appendMessageUI("assistant", welcomeHTML);
  }

  async handleSendMessage() {
    const text = this.chatInputElem.value.trim();
    if (!text || !this.currentSessionId) return;

    this.chatInputElem.value = "";

    // 1. Render User Message immediately
    this.appendMessageUI("user", text);

    // 2. Render Thinking Bubble
    const thinkingId = this.appendThinkingUI();

    // 3. Send API request
    const providerOverride = this.providerSelectElem.value;

    try {
      const response = await api.sendChatMessage(this.currentSessionId, text, providerOverride);
      this.removeMessageUI(thinkingId);

      const assistantMsg = response.assistant_message;
      const artifactsList = response.artifact ? [response.artifact] : [];

      this.appendMessageUI("assistant", assistantMsg.content, assistantMsg.citations, artifactsList);

      // Auto open artifact viewer if artifact created
      if (response.artifact) {
        this.viewer.open(response.artifact);
      }

      await this.loadSessions();
    } catch (e) {
      this.removeMessageUI(thinkingId);
      this.appendMessageUI("assistant", "⚠️ **Service Error**: Failed to reach assistant backend. Please verify server status.");
      console.error("Chat dispatch error:", e);
    }
  }

  appendMessageUI(role, text, citations = [], artifacts = []) {
    const row = document.createElement("div");
    row.className = `message-row ${role}`;
    const msgId = "msg-" + Math.random().toString(36).substr(2, 9);
    row.id = msgId;

    const assistantSvg = `<svg width="18" height="18" viewBox="0 0 100 100" fill="none"><path d="M 31 27 L 42 27 L 47 48 L 88 13 L 55 45 L 46 62 Z" fill="#FFFFFF"/><path d="M 64 30 C 76 30 82 40 82 49 C 82 60 70 66 57 66 L 22 95 L 45 60 C 58 60 71 56 71 49 C 71 43 66 38 60 38 Z" fill="#FFFFFF"/></svg>`;
    const avatarText = role === "user" ? "👤" : assistantSvg;
    const formattedContent = this.formatMarkdown(text);

    let citationsHTML = "";
    if (citations && citations.length > 0) {
      citationsHTML = `<div class="citations-container">`;
      citations.forEach(c => {
        citationsHTML += `
          <div class="citation-pill" title="${this.escapeHtml(c.snippet)}">
            📖 ${this.escapeHtml(c.guest)} (${c.start_timestamp})
          </div>
        `;
      });
      citationsHTML += `</div>`;
    }

    let artifactsHTML = "";
    if (artifacts && artifacts.length > 0) {
      artifacts.forEach(art => {
        artifactsHTML += `
          <div class="artifact-card" data-art-id="${art.id}">
            <div>
              <div style="font-weight: 600; font-size: 0.9rem; color: #A7F3D0;">🎨 ${this.escapeHtml(art.title)}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">Click to open Sandboxed Artifact Viewer</div>
            </div>
            <span style="font-size: 0.8rem; color: var(--accent-indigo);">Open Viewer &rarr;</span>
          </div>
        `;
      });
    }

    row.innerHTML = `
      <div class="avatar">${avatarText}</div>
      <div class="bubble">
        ${formattedContent}
        ${citationsHTML}
        ${artifactsHTML}
      </div>
    `;

    this.chatStreamElem.appendChild(row);
    this.chatStreamElem.scrollTop = this.chatStreamElem.scrollHeight;

    // Attach click listeners to artifact cards
    row.querySelectorAll(".artifact-card").forEach(card => {
      card.addEventListener("click", async () => {
        const artId = card.getAttribute("data-art-id");
        if (artId) {
          try {
            const artData = await api.getArtifact(artId);
            this.viewer.open(artData);
          } catch (e) {
            console.error("Failed to fetch artifact for viewer:", e);
          }
        }
      });
    });

    return msgId;
  }

  appendThinkingUI() {
    const row = document.createElement("div");
    row.className = "message-row assistant";
    const id = "thinking-" + Math.random().toString(36).substr(2, 9);
    row.id = id;

    row.innerHTML = `
      <div class="avatar"><svg width="18" height="18" viewBox="0 0 100 100" fill="none"><path d="M 31 27 L 42 27 L 47 48 L 88 13 L 55 45 L 46 62 Z" fill="#FFFFFF"/><path d="M 64 30 C 76 30 82 40 82 49 C 82 60 70 66 57 66 L 22 95 L 45 60 C 58 60 71 56 71 49 C 71 43 66 38 60 38 Z" fill="#FFFFFF"/></svg></div>
      <div class="bubble" style="color: var(--text-muted); font-style: italic;">
        Agent thinking & processing response...
      </div>
    `;

    this.chatStreamElem.appendChild(row);
    this.chatStreamElem.scrollTop = this.chatStreamElem.scrollHeight;
    return id;
  }

  removeMessageUI(msgId) {
    const elem = document.getElementById(msgId);
    if (elem) elem.remove();
  }

  formatMarkdown(text) {
    if (!text) return "";
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Headings
    html = html.replace(/^### (.*$)/gim, '<h3 style="margin-top: 1rem; color: #8B5CF6;">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 style="margin-top: 1.2rem; color: #A7F3D0;">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 style="margin-top: 1.5rem; color: #FFFFFF;">$1</h1>');

    // Bold & Italics
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Bullets
    html = html.replace(/^\- (.*$)/gim, '<li style="margin-left: 1.2rem;">$1</li>');

    // Linebreaks
    html = html.replace(/\n/g, '<br>');

    return html;
  }

  escapeHtml(str) {
    if (!str) return "";
    return str.replace(/[&<>"']/g, m => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    })[m]);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.app = new App();
});
