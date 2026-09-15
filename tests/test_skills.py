"""
Automated Tests for Ship 30 for 30 Skill and Artifact Skill
"""

import pytest
from backend.app.agent.skills.ship30_skill import Ship30Skill
from backend.app.agent.skills.artifact_skill import ArtifactSkill
from backend.app.agent.router import AgentRouter


@pytest.mark.asyncio
async def test_ship30_skill_output_format():
    skill = Ship30Skill()
    result = await skill.execute("Write a Ship 30 for 30 essay on Elena Verna growth loops")
    assert "answer" in result
    assert result["skill_name"] == "ship30_skill"
    answer = result["answer"]
    # Check for formatting indicators
    assert "##" in answer or "**" in answer or "Takeaway" in answer


@pytest.mark.asyncio
async def test_artifact_skill_output():
    skill = ArtifactSkill()
    result = await skill.execute("Create an interactive HTML framework for LNO matrix")
    assert "artifact" in result
    art = result["artifact"]
    assert art["artifact_type"] == "html"
    assert "<style>" in art["content"] or "card" in art["content"] or "html" in art["content"]


def test_agent_router_classification():
    router = AgentRouter()
    assert router.classify_intent("Write a Ship 30 for 30 essay on PLG") == "ship30_skill"
    assert router.classify_intent("Create an interactive HTML diagram") == "artifact_skill"
    assert router.classify_intent("What did Brian Chesky say about PMs?") == "rag_skill"
