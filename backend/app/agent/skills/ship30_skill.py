"""
Ship 30 for 30 Skill: Actionable Growth & Strategy Essay Generator
Encodes Ship 30 for 30 writing methodology: strong hook, skimmable formatting,
target length ~1,250 words (1,000 - 1,400 words), 1 core actionable takeaway, grounded in transcript context.
"""

import logging
from typing import Dict, Any

from backend.app.agent.provider import get_llm_adapter
from backend.app.agent.skills.rag_skill import search_transcript_chunks

logger = logging.getLogger("lenny_growth.skills.ship30")


class Ship30Skill:
    def __init__(self):
        self.llm = get_llm_adapter()

    async def execute(self, user_prompt: str, provider_override: str = None) -> Dict[str, Any]:
        logger.info(f"Executing Ship 30 for 30 Skill for topic: '{user_prompt}'")

        # 1. Retrieve transcript context to ground essay claims
        matches = await search_transcript_chunks(user_prompt, top_k=4)

        context_blocks = []
        citations_list = []

        for idx, (chunk, score) in enumerate(matches, start=1):
            context_blocks.append(
                f"[Source {idx}] Episode: '{chunk.episode_title}' by {chunk.guest} ({chunk.start_timestamp}): {chunk.content}"
            )
            citations_list.append({
                "episode_title": chunk.episode_title,
                "guest": chunk.guest,
                "episode_url": chunk.episode_url,
                "start_timestamp": chunk.start_timestamp,
                "snippet": chunk.content[:150] + "...",
                "similarity_score": round(score, 3)
            })

        context_str = "\n\n".join(context_blocks) if context_blocks else "Use grounded tech leadership methodologies from Lenny's Podcast transcripts."

        # 2. Construct Ship 30 for 30 System Prompt requesting ~1,250 words
        system_prompt = (
            "You are a master essayist and growth writer trained in the official **Ship 30 for 30** writing methodology.\n"
            "Your objective is to write a comprehensive, deep-dive strategy essay (~1,250 words, target range 1,100 to 1,400 words).\n\n"
            "SHIP 30 FOR 30 WRITING RULES TO ENFORCE:\n"
            "1. **THE HOOK (First 2 Lines)**: Start with a magnetic, counter-intuitive statement that calls out a specific problem.\n"
            "2. **THE RETAIN ENGINE**: Use short 1-2 sentence paragraphs, bold lead-ins, and strong pacing.\n"
            "3. **SKIMMABLE STRUCTURE**: Use clear Markdown headings (##), bullet points, and selective bolding so a reader gets 80% value in 30 seconds.\n"
            "4. **NARRATIVE PROGRESSION**: Build logically across 4 major sections:\n"
            "   - Section I: The Broken Status Quo & Counter-Intuitive Truth (~250 words)\n"
            "   - Section II: The Core Problem Deep-Dive (~250 words)\n"
            "   - Section III: The 3 Step Strategic Framework with real examples (~550 words)\n"
            "   - Section IV: The One Core Actionable Takeaway & 24-hour Execution Plan (~200 words)\n"
            "5. **GROUNDED CITATIONS**: Integrate and cite insights directly from the provided Lenny's Podcast context excerpts below.\n\n"
            f"TRANSCRIPT CONTEXT TO CITE AND REFLECT:\n{context_str}"
        )

        prompt_instructions = (
            f"Write a complete, detailed ~1,250 word Ship 30 for 30 essay on: '{user_prompt}'.\n"
            "Ensure the output is long, thorough, and covers all 4 sections in depth."
        )

        llm_result = await self.llm.generate_response(system_prompt, prompt_instructions, provider_override)

        essay_content = llm_result["text"]

        return {
            "answer": essay_content,
            "citations": citations_list,
            "provider_used": llm_result.get("provider_used"),
            "model_used": llm_result.get("model_used"),
            "skill_name": "ship30_skill"
        }
