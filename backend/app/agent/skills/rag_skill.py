"""
RAG Skill: Grounded Transcript Retrieval & Citation Answering
Searches vector index in Postgres pgvector, with local transcript dataset fallback if DB is unreachable.
"""

import os
import glob
import json
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from sqlalchemy import select

from backend.app.agent.embeddings import get_embedding_generator
from backend.app.agent.provider import get_llm_adapter
from backend.app.config import get_settings
from backend.app.db import AsyncSessionLocal
from backend.app.models import TranscriptChunk

logger = logging.getLogger("lenny_growth.skills.rag")
settings = get_settings()


def load_local_transcript_chunks() -> List[TranscriptChunk]:
    """Fallback loader for ingestion/data/ transcript JSON files."""
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "ingestion", "data"))
    files = glob.glob(os.path.join(data_dir, "*.json"))
    chunks_list = []
    embedder = get_embedding_generator()

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            title = data.get("episode_title", "")
            guest = data.get("guest", "")
            url = data.get("episode_url", "")
            for chunk in data.get("chunks", []):
                content = chunk.get("content", "")
                emb = embedder.embed_text(content)
                tc = TranscriptChunk(
                    episode_title=title,
                    guest=guest,
                    episode_url=url,
                    start_timestamp=chunk.get("start_timestamp", "00:00"),
                    content=content,
                    embedding=emb
                )
                chunks_list.append(tc)
    return chunks_list


async def search_transcript_chunks(query_text: str, top_k: int = 4) -> List[Tuple[TranscriptChunk, float]]:
    """Performs vector search across transcript chunks in database, falling back to local files if DB is offline."""
    embedder = get_embedding_generator()
    query_vector = embedder.embed_text(query_text)

    all_chunks = []
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(TranscriptChunk))
            all_chunks = result.scalars().all()
    except Exception as e:
        logger.warning(f"PostgreSQL connection offline ({e}). Using local transcript dataset fallback.")
        all_chunks = load_local_transcript_chunks()

    if not all_chunks:
        return []

    matches = []
    for chunk in all_chunks:
        if chunk.embedding is not None:
            c_vec = np.array(chunk.embedding)
            q_vec = np.array(query_vector)
            norm_c = np.linalg.norm(c_vec)
            norm_q = np.linalg.norm(q_vec)

            if norm_c > 0 and norm_q > 0:
                sim = float(np.dot(q_vec, c_vec) / (norm_q * norm_c))
            else:
                sim = 0.0
        else:
            sim = 0.0
        matches.append((chunk, sim))

    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:top_k]


class RAGSkill:
    def __init__(self):
        self.llm = get_llm_adapter()

    async def execute(self, user_query: str, provider_override: str = None) -> Dict[str, Any]:
        logger.info(f"Executing RAG Skill for query: '{user_query}'")

        # 1. Retrieve top matching chunks
        matches = await search_transcript_chunks(user_query, top_k=settings.TOP_K_CHUNKS)

        valid_matches = [(chunk, score) for chunk, score in matches if score >= settings.SIMILARITY_THRESHOLD]

        if not valid_matches and matches:
            top_score = matches[0][1]
            if top_score > 0.1:
                valid_matches = matches[:2]

        if not valid_matches:
            logger.info("No matching chunks met similarity threshold. Triggering explicit refusal.")
            return {
                "answer": (
                    "I searched Lenny's Podcast transcript index, but I couldn't find any relevant transcript evidence "
                    "or discussion matching your question.\n\n"
                    "*To prevent hallucination, I only answer questions that are grounded in verified podcast transcripts.*"
                ),
                "citations": [],
                "skill_name": "rag_skill"
            }

        # 2. Format context & citations
        context_blocks = []
        citations_list = []

        for idx, (chunk, score) in enumerate(valid_matches, start=1):
            block = (
                f"--- SOURCE [{idx}] ---\n"
                f"Episode: {chunk.episode_title}\n"
                f"Guest: {chunk.guest}\n"
                f"Timestamp: {chunk.start_timestamp}\n"
                f"Content: {chunk.content}\n"
            )
            context_blocks.append(block)

            citations_list.append({
                "episode_title": chunk.episode_title,
                "guest": chunk.guest,
                "episode_url": chunk.episode_url,
                "start_timestamp": chunk.start_timestamp,
                "snippet": chunk.content[:150] + "...",
                "similarity_score": round(score, 3)
            })

        context_str = "\n".join(context_blocks)

        system_prompt = (
            "You are 'The Lenny Growth Assistant', an expert AI advisor for Product Managers and Growth leaders.\n"
            "Answer the user's question using ONLY the provided transcript excerpts below.\n"
            "REQUIREMENTS:\n"
            "1. Be precise, highly structured, and actionable.\n"
            "2. Ground every major claim directly in provided sources.\n"
            "3. Cite your sources inline using [Episode Title - Guest].\n"
            "4. If source material is insufficient, state that explicitly.\n\n"
            f"PROVIDED TRANSCRIPT CONTEXT:\n{context_str}"
        )

        user_prompt = f"User Question: {user_query}"

        llm_result = await self.llm.generate_response(system_prompt, user_prompt, provider_override)

        return {
            "answer": llm_result["text"],
            "citations": citations_list,
            "provider_used": llm_result.get("provider_used"),
            "model_used": llm_result.get("model_used"),
            "skill_name": "rag_skill"
        }
