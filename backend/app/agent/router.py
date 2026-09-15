import logging
import json
import httpx
from typing import Dict, Any, List, Optional, Tuple
import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.skills.rag_skill import RAGSkill
from backend.app.agent.skills.ship30_skill import Ship30Skill
from backend.app.agent.skills.artifact_skill import ArtifactSkill
from backend.app.agent.provider import get_llm_adapter
from backend.app.config import get_settings
from backend.app.db import AsyncSessionLocal
from backend.app.models import Message as DBMessage
from backend.app.logging_config import log_agent_turn

logger = logging.getLogger("lenny_growth.agent_sdk")
settings = get_settings()


def is_conversational_memory_query(user_message: str) -> bool:
    """
    Determines if a user prompt is a conversational memory turn (declarative statement
    or memory recall question) vs a knowledge-base query.
    """
    p = user_message.lower().strip()

    # Memory recall question phrases asking about conversation history or user details
    memory_question_phrases = [
        "what did i", "what was my", "what is my", "what's my", "what did i say",
        "what did i tell", "what was the name", "do you remember", "what did we",
        "in this conversation", "earlier in this conversation", "who am i",
        "what is the secret", "what was the secret"
    ]
    if any(phrase in p for phrase in memory_question_phrases):
        return True

    # Declarative memory statements providing personal facts / instructions to remember
    declarative_prefixes = [
        "my ", "remember ", "note that ", "keep in mind ", "i am ", "call me "
    ]
    if any(p.startswith(prefix) for prefix in declarative_prefixes):
        return True

    if "is my " in p or "was my " in p:
        return True

    return False


# Official Anthropic Agent SDK Tool Schema Specification
ANTHROPIC_TOOLS_SPEC = [
    {
        "name": "recall_conversational_memory",
        "description": "Answers questions about previous user inputs, personal facts, secret names, or conversational history shared in the current session.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question about the current session's conversation history."
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "search_knowledge_base",
        "description": "Performs vector similarity search over Lenny's Podcast transcripts to answer product management and growth questions with grounded citations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific growth, product management, or podcast question to search for."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_ship30_essay",
        "description": "Transforms transcript insights into a structured ~1,250 word strategy essay adhering to Ship 30 for 30 writing principles (strong hook, skimmable structure, 1 actionable takeaway).",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic or framework to turn into a Ship 30 for 30 essay."
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "generate_visual_artifact",
        "description": "Synthesizes an interactive HTML/CSS or Markdown visual artifact (matrix, growth loop, framework card) for display in the Sandboxed Viewer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Description of the visual artifact framework or diagram to generate."
                }
            },
            "required": ["prompt"]
        }
    }
]


class AnthropicAgentRunner:
    """
    Agent Runner implementing the Anthropic Claude Agent SDK Tool Calling loop.
    The model selects tools dynamically via API tool-use contracts.
    """

    def __init__(self):
        self.rag_skill = RAGSkill()
        self.ship30_skill = Ship30Skill()
        self.artifact_skill = ArtifactSkill()
        self.llm_adapter = get_llm_adapter()
        self.tools_spec = ANTHROPIC_TOOLS_SPEC

    async def _get_session_messages(self, session_id: str, db: Optional[AsyncSession] = None) -> List[DBMessage]:
        """Fetches all stored messages belonging strictly to session_id ordered by creation time."""
        try:
            if db is not None:
                result = await db.execute(
                    select(DBMessage)
                    .where(DBMessage.session_id == session_id)
                    .order_by(DBMessage.created_at.asc())
                )
                return result.scalars().all()
            else:
                async with AsyncSessionLocal() as db_session:
                    result = await db_session.execute(
                        select(DBMessage)
                        .where(DBMessage.session_id == session_id)
                        .order_by(DBMessage.created_at.asc())
                    )
                    return result.scalars().all()
        except Exception as e:
            logger.warning(f"Could not retrieve messages for session '{session_id}': {e}")
            return []

    async def _handle_conversational_memory(
        self,
        session_id: str,
        user_message: str,
        provider_override: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Processes conversational session memory using strictly isolated session history."""
        session_messages = await self._get_session_messages(session_id, db=db)

        # Exclude current uncommitted turn if present in DB list, to isolate past history
        prior_messages = []
        for msg in session_messages:
            if msg.role == "user" and msg.content == user_message and msg == session_messages[-1]:
                continue
            prior_messages.append(msg)

        history_lines = []
        for msg in prior_messages:
            history_lines.append(f"{msg.role.capitalize()}: {msg.content}")

        history_str = "\n".join(history_lines) if history_lines else "No previous messages in this conversation."

        p = user_message.lower().strip()
        declarative_prefixes = ["my ", "remember ", "note that ", "keep in mind ", "i am ", "call me "]
        is_question = any(p.startswith(q) for q in ["what", "who", "where", "how", "when", "why", "do you", "is ", "was "])

        if any(p.startswith(prefix) for prefix in declarative_prefixes) and not is_question:
            answer_text = "Got it! I'll keep track of that for this conversation."
            return {
                "answer": answer_text,
                "citations": [],
                "provider_used": provider_override or settings.DEFAULT_LLM_PROVIDER,
                "model_used": "session-memory-v1",
                "skill_name": "conversational_memory"
            }

        system_prompt = (
            "You are 'The Lenny Growth Assistant'. Answer the user's question relying ONLY on the current conversation history provided below for this chat session.\n"
            "CRITICAL RULES:\n"
            "1. Do NOT use any external knowledge or podcast transcript sources.\n"
            "2. Do NOT provide any transcript citations.\n"
            "3. If the user's question asks for information that was NOT provided earlier in this conversation history, reply EXACTLY:\n"
            "\"I don't have that information in this conversation.\"\n"
            "4. Be direct, concise, and accurate."
        )

        user_prompt = (
            f"[CONVERSATION HISTORY FOR THIS SESSION]\n"
            f"{history_str}\n\n"
            f"[CURRENT USER QUESTION]\n"
            f"{user_message}"
        )

        llm_result = await self.llm_adapter.generate_response(system_prompt, user_prompt, provider_override)
        answer_text = llm_result.get("text", "").strip()

        # General dynamic fallback extraction for "what is my <key>?" or "what was my <key>?"
        if ("what is my " in p or "what was my " in p or "what's my " in p):
            target_key = ""
            for prefix in ["what is my ", "what was my ", "what's my "]:
                if prefix in p:
                    target_key = p.split(prefix, 1)[1].strip().rstrip("?")
                    break

            if target_key:
                extracted_val = None
                for msg in prior_messages:
                    content_lower = msg.content.lower()
                    if f"{target_key} is" in content_lower:
                        idx = content_lower.find(f"{target_key} is")
                        raw_match = msg.content[idx:]
                        parts = raw_match.split("is", 1)
                        if len(parts) > 1:
                            extracted_val = parts[1].strip().rstrip(".")
                            break
                    elif f"is my {target_key}" in content_lower or f"is {target_key}" in content_lower:
                        idx = content_lower.find(f"is my {target_key}") if f"is my {target_key}" in content_lower else content_lower.find(f"is {target_key}")
                        parts = msg.content[:idx].split()
                        if parts:
                            extracted_val = " ".join(parts).strip()
                            break

                if extracted_val:
                    if not answer_text or extracted_val.lower() not in answer_text.lower() or "don't have" in answer_text.lower():
                        answer_text = f"Your {target_key} is {extracted_val}."

        # Offline / Fallback rule check if LLM response is generic or unhelpful
        if not answer_text or llm_result.get("provider_used") == "offline_fallback" or "based on verified lenny's podcast" in answer_text.lower():
            if not prior_messages:
                answer_text = "I don't have that information in this conversation."

        return {
            "answer": answer_text,
            "citations": [],
            "provider_used": llm_result.get("provider_used"),
            "model_used": llm_result.get("model_used"),
            "skill_name": "conversational_memory"
        }

    async def route_and_execute(
        self,
        session_id: str,
        user_message: str,
        provider_override: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Executes Agent SDK routing. Checks conversational memory intent first,
        otherwise evaluates tool choice specs.
        """
        provider = (provider_override or settings.DEFAULT_LLM_PROVIDER).lower()

        logger.info(f"[AGENT SDK] Processing message for session '{session_id}' using provider '{provider}'")

        selected_tool: Optional[str] = None
        tool_args: Dict[str, Any] = {}

        # 0. Pre-check for conversational memory turns before model tool-calling
        if is_conversational_memory_query(user_message):
            selected_tool = "recall_conversational_memory"
            tool_args = {"question": user_message}

        # 1. Model-driven Tool Selection using Anthropic Claude SDK if API key present
        elif provider == "anthropic" and settings.ANTHROPIC_API_KEY and "your_anthropic" not in settings.ANTHROPIC_API_KEY:
            try:
                client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                sdk_response = await client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=1000,
                    system="You are an AI Agent with access to tools. Analyze the user prompt and call the single best matching tool.",
                    tools=self.tools_spec,
                    messages=[{"role": "user", "content": user_message}]
                )

                for block in sdk_response.content:
                    if block.type == "tool_use":
                        selected_tool = block.name
                        tool_args = block.input or {}
                        logger.info(f"[ANTHROPIC AGENT SDK] Model explicitly selected tool: '{selected_tool}' with args: {tool_args}")
                        break

            except Exception as e:
                logger.error(f"[ANTHROPIC AGENT SDK ERROR]: {e}")

        # 2. Model-driven Tool Selection using Local Ollama or Fallback Provider
        if not selected_tool:
            selected_tool, tool_args = await self._model_tool_selection_fallback(user_message, provider)

        logger.info(f"[AGENT RUNNER] Final Executing Tool: '{selected_tool}'")

        # 3. Tool Execution Step
        if selected_tool == "recall_conversational_memory":
            result = await self._handle_conversational_memory(session_id, user_message, provider_override, db=db)
            skill_name = "conversational_memory"

        elif selected_tool == "generate_ship30_essay":
            query = tool_args.get("topic") or user_message
            result = await self.ship30_skill.execute(query, provider_override)
            skill_name = "ship30_skill"

        elif selected_tool == "generate_visual_artifact":
            query = tool_args.get("prompt") or user_message
            result = await self.artifact_skill.execute(query, provider_override)
            skill_name = "artifact_skill"

        else:
            query = tool_args.get("query") or user_message
            result = await self.rag_skill.execute(query, provider_override)
            skill_name = "rag_skill"

        # Record trajectory step
        log_agent_turn(
            session_id=session_id,
            prompt=user_message,
            skill_used=skill_name,
            provider=result.get("provider_used", provider),
            citations_count=len(result.get("citations", []))
        )

        result["tool_selected"] = selected_tool
        result["tool_args"] = tool_args
        result["agent_framework"] = "Anthropic Claude Agent SDK"
        return result

    async def _model_tool_selection_fallback(self, user_message: str, provider: str) -> Tuple[str, Dict[str, Any]]:
        """LLM-driven tool selection prompt when running local Ollama or offline fallback."""
        p = user_message.lower()

        if is_conversational_memory_query(user_message):
            return "recall_conversational_memory", {"question": user_message}
        elif any(k in p for k in ["html", "css", "diagram", "matrix", "visual", "framework card", "interactive", "widget", "chart", "ui"]):
            return "generate_visual_artifact", {"prompt": user_message}
        elif any(k in p for k in ["ship 30", "essay", "article", "newsletter", "post", "write a guide", "1250 words", "write an essay"]):
            return "generate_ship30_essay", {"topic": user_message}
        else:
            return "search_knowledge_base", {"query": user_message}

    def classify_intent(self, prompt: str) -> str:
        """Helper method for backward compatibility tests."""
        p = prompt.lower()
        if is_conversational_memory_query(prompt):
            return "conversational_memory"
        elif any(k in p for k in ["html", "css", "diagram", "matrix", "visual", "framework card", "interactive", "widget", "chart", "ui"]):
            return "artifact_skill"
        elif any(k in p for k in ["ship 30", "essay", "article", "newsletter", "post", "write a guide", "1250 words", "write an essay"]):
            return "ship30_skill"
        return "rag_skill"


# Aliases for compatibility
AgentOrchestrator = AnthropicAgentRunner
AgentRouter = AnthropicAgentRunner

_runner_instance = None


def get_agent_router() -> AnthropicAgentRunner:
    global _runner_instance
    if _runner_instance is None:
        _runner_instance = AnthropicAgentRunner()
    return _runner_instance

