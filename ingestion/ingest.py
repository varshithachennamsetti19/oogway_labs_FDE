#!/usr/bin/env python3
"""
Transcript Ingestion CLI Script
Ingests JSON transcript files from ingestion/data/, extracts chunks,
computes vector embeddings, and populates PostgreSQL pgvector database.
"""

import os
import sys
import json
import glob
import asyncio
import argparse
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.agent.embeddings import get_embedding_generator
from backend.app.config import get_settings
from backend.app.db import AsyncSessionLocal, init_db, engine
from backend.app.models import TranscriptChunk
from sqlalchemy import select, func


def load_transcript_files(data_dir: str) -> List[Dict[str, Any]]:
    """Loads all transcript JSON files from data directory."""
    files = glob.glob(os.path.join(data_dir, "*.json"))
    transcripts = []
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            transcripts.append(data)
    return transcripts


async def ingest_transcripts(data_dir: str, check_only: bool = False):
    """Parses transcript files, computes embeddings, and stores in database."""
    print(f"🔍 Searching for transcript data in '{data_dir}'...")
    transcripts = load_transcript_files(data_dir)
    print(f"📦 Loaded {len(transcripts)} transcript files.")

    embedder = get_embedding_generator()
    print(f"🧠 Embedder initialized: model='{embedder.model_name}', dimension={embedder.dimension}")

    all_chunks_to_insert = []
    total_chunks = 0

    for item in transcripts:
        title = item.get("episode_title", "Unknown Episode")
        guest = item.get("guest", "Unknown Guest")
        url = item.get("episode_url", "")
        topics = item.get("topics", [])
        chunks = item.get("chunks", [])

        print(f"  📄 Processing: '{title}' ({len(chunks)} chunks)")

        for chunk in chunks:
            timestamp = chunk.get("start_timestamp", "00:00")
            text = chunk.get("content", "")

            # Compute vector embedding
            embedding_vector = embedder.embed_text(text)

            chunk_record = {
                "episode_title": title,
                "guest": guest,
                "episode_url": url,
                "start_timestamp": timestamp,
                "content": text,
                "embedding": embedding_vector,
                "metadata_json": {"topics": topics}
            }
            all_chunks_to_insert.append(chunk_record)
            total_chunks += 1

    print(f"✅ Computed embeddings for {total_chunks} transcript chunks.")

    if check_only:
        print("🔍 Dry run complete. Database insertion skipped.")
        return

    print("⚡ Initializing database schema & pgvector extension...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check existing count
        result = await session.execute(select(func.count()).select_from(TranscriptChunk))
        count_before = result.scalar()

        print(f"📊 Current chunks in database: {count_before}")

        # Clear existing or upsert
        for record in all_chunks_to_insert:
            db_chunk = TranscriptChunk(
                episode_title=record["episode_title"],
                guest=record["guest"],
                episode_url=record["episode_url"],
                start_timestamp=record["start_timestamp"],
                content=record["content"],
                embedding=record["embedding"],
                metadata_json=record["metadata_json"]
            )
            session.add(db_chunk)

        await session.commit()

        result = await session.execute(select(func.count()).select_from(TranscriptChunk))
        count_after = result.scalar()
        print(f"🎉 Success! Database now contains {count_after} transcript chunks.")


def main():
    parser = argparse.ArgumentParser(description="Ingest Lenny's Podcast transcripts into pgvector.")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "data"), help="Path to transcript JSON files")
    parser.add_argument("--check", action="store_true", help="Perform dry-run parsing and embedding without database insertion")

    args = parser.parse_args()
    asyncio.run(ingest_transcripts(args.data_dir, check_only=args.check))


if __name__ == "__main__":
    main()
