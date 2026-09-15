"""
Automated Tests for LLM Provider Adapter & Fallbacks
"""

import pytest
from backend.app.agent.provider import LLMProviderAdapter


@pytest.mark.asyncio
async def test_provider_fallback_chain():
    adapter = LLMProviderAdapter()
    # Test requesting unknown or unconfigured provider triggers fallback without error
    result = await adapter.generate_response(
        system_prompt="You are a helpful assistant.",
        user_prompt="Explain product growth.",
        provider_override="unconfigured_provider"
    )
    assert "text" in result
    assert "provider_used" in result
    assert len(result["text"]) > 0
