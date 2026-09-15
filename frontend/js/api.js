/**
 * API Client Module for FastAPI Backend
 */

const API_BASE = ""; // Relative path for unified FastAPI deployment

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health/llm`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.error("Health check error:", e);
  }
  return { status: "offline", active_provider: "unknown", available_providers: [] };
}

export async function getSessions() {
  const res = await fetch(`${API_BASE}/api/sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return await res.json();
}

export async function createSession(title = "New Growth Chat") {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title })
  });
  if (!res.ok) throw new Error("Failed to create session");
  return await res.json();
}

export async function getSessionMessages(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error("Failed to fetch session messages");
  return await res.json();
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE"
  });
  if (!res.ok) throw new Error("Failed to delete session");
  return true;
}

export async function sendChatMessage(sessionId, message, providerOverride = null) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
      provider_override: providerOverride
    })
  });
  if (!res.ok) throw new Error("Failed to send chat message");
  return await res.json();
}

export async function getArtifact(artifactId) {
  const res = await fetch(`${API_BASE}/api/artifacts/${artifactId}`);
  if (!res.ok) throw new Error("Failed to fetch artifact");
  return await res.json();
}
