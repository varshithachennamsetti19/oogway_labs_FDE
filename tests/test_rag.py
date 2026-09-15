"""
Automated Tests for RAG Skill Grounding & Refusal Behavior
"""

import pytest
from backend.app.agent.skills.rag_skill import RAGSkill


@pytest.mark.asyncio
async def test_rag_grounded_answer():
    skill = RAGSkill()
    # Query matching ingested Shreyas Doshi transcript
    result = await skill.execute("What is Shreyas Doshi's LNO framework?")
    assert "answer" in result
    assert "citations" in result
    assert isinstance(result["citations"], list)
    assert result["skill_name"] == "rag_skill"


@pytest.mark.asyncio
async def test_rag_explicit_refusal():
    skill = RAGSkill()
    # Query completely outside scope
    result = await skill.execute("What is the recipe for chocolate chip cookies in Paris?")
    assert "answer" in result
    assert "couldn't find any relevant transcript evidence" in result.get("answer", "").lower() or len(result.get("citations", [])) == 0
