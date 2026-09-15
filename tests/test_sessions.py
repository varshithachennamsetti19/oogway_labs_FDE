"""
Automated Tests for Session Management, Session Memory & Isolation
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_session_crud():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Session
        create_res = await ac.post("/api/sessions", json={"title": "Test Strategy Session"})
        assert create_res.status_code == 201
        session_data = create_res.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Test Strategy Session"

        # 2. List Sessions
        list_res = await ac.get("/api/sessions")
        assert list_res.status_code == 200
        sessions_list = list_res.json()
        assert any(s["id"] == session_id for s in sessions_list)

        # 3. Get Session Messages
        msg_res = await ac.get(f"/api/sessions/{session_id}/messages")
        assert msg_res.status_code == 200
        messages_data = msg_res.json()
        assert messages_data["id"] == session_id
        assert isinstance(messages_data["messages"], list)

        # 4. Delete Session
        del_res = await ac.delete(f"/api/sessions/{session_id}")
        assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_session_isolation_secret_name():
    """TEST 1 — Session isolation: Session B does NOT receive Session A's secret project name."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create Session A
        res_a = await ac.post("/api/sessions", json={"title": "Session A"})
        session_a_id = res_a.json()["id"]

        # Add "Project Falcon" to Session A
        await ac.post("/api/chat", json={
            "session_id": session_a_id,
            "message": "My secret project name is Project Falcon."
        })

        # Create Session B
        res_b = await ac.post("/api/sessions", json={"title": "Session B"})
        session_b_id = res_b.json()["id"]

        # Ask B "What is my secret project name?"
        chat_b_res = await ac.post("/api/chat", json={
            "session_id": session_b_id,
            "message": "What is my secret project name?"
        })
        assert chat_b_res.status_code == 200
        answer_b = chat_b_res.json()["assistant_message"]["content"]

        # Verify B does NOT receive "Project Falcon"
        assert "Falcon" not in answer_b
        assert "don't have" in answer_b.lower() or "no" in answer_b.lower() or "falcon" not in answer_b.lower()


@pytest.mark.asyncio
async def test_session_persistence_secret_name():
    """TEST 2 — Session persistence: Session A remembers Project Falcon in subsequent turn."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create Session A
        res_a = await ac.post("/api/sessions", json={"title": "Session A Persistence"})
        session_a_id = res_a.json()["id"]

        # Add "Project Falcon" to Session A
        await ac.post("/api/chat", json={
            "session_id": session_a_id,
            "message": "My secret project name is Project Falcon."
        })

        # Reload / Ask Session A "What is my secret project name?"
        ask_res = await ac.post("/api/chat", json={
            "session_id": session_a_id,
            "message": "What is my secret project name?"
        })
        assert ask_res.status_code == 200
        answer_a = ask_res.json()["assistant_message"]["content"]

        # Verify the answer uses Session A's conversation history
        assert "Falcon" in answer_a


@pytest.mark.asyncio
async def test_no_cross_session_leakage():
    """TEST 3 — No cross-session leakage: Session A has Alpha, Session B has Beta."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Session A with unique info
        res_a = await ac.post("/api/sessions", json={"title": "Session Alpha"})
        session_a_id = res_a.json()["id"]
        await ac.post("/api/chat", json={
            "session_id": session_a_id,
            "message": "My secret project name is Project Alpha."
        })

        # Session B with unique info
        res_b = await ac.post("/api/sessions", json={"title": "Session Beta"})
        session_b_id = res_b.json()["id"]
        await ac.post("/api/chat", json={
            "session_id": session_b_id,
            "message": "My secret project name is Project Beta."
        })

        # Query Session A
        query_a = await ac.post("/api/chat", json={
            "session_id": session_a_id,
            "message": "What is my secret project name?"
        })
        ans_a = query_a.json()["assistant_message"]["content"]
        assert "alpha" in ans_a.lower()
        assert "beta" not in ans_a.lower()

        # Query Session B
        query_b = await ac.post("/api/chat", json={
            "session_id": session_b_id,
            "message": "What is my secret project name?"
        })
        ans_b = query_b.json()["assistant_message"]["content"]
        assert "beta" in ans_b.lower()
        assert "alpha" not in ans_b.lower()


@pytest.mark.asyncio
async def test_memory_questions_bypass_rag():
    """TEST 4 — Memory questions bypass RAG: No transcript citations attached."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/sessions", json={"title": "RAG Bypass Test"})
        session_id = res.json()["id"]

        chat_res = await ac.post("/api/chat", json={
            "session_id": session_id,
            "message": "What is my secret project name?"
        })
        assert chat_res.status_code == 200
        citations = chat_res.json()["assistant_message"]["citations"]

        # Verify no transcript retrieval/citations are attached
        assert len(citations) == 0
        assert chat_res.json()["skill_used"] == "conversational_memory"


@pytest.mark.asyncio
async def test_rag_remains_unchanged_for_kb_questions():
    """TEST 5 — RAG remains unchanged for actual knowledge-base questions."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/sessions", json={"title": "RAG Test"})
        session_id = res.json()["id"]

        chat_res = await ac.post("/api/chat", json={
            "session_id": session_id,
            "message": "What is Shreyas Doshi's LNO framework?"
        })
        assert chat_res.status_code == 200
        data = chat_res.json()

        assert data["skill_used"] == "rag_skill"
        assert len(data["assistant_message"]["citations"]) > 0

