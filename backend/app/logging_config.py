"""
Structured Logging & Agent Transcript Logger
Logs application events, RAG retrieval steps, and LLM calls.
"""

import os
import sys
import logging
from datetime import datetime


def setup_logging():
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agent-transcripts"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "runtime_logs.log")

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # File Handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    return root_logger


def log_agent_turn(session_id: str, prompt: str, skill_used: str, provider: str, citations_count: int):
    """Utility to record structured agent turn metadata."""
    logger = logging.getLogger("lenny_growth.agent_transcript")
    timestamp = datetime.utcnow().isoformat()
    log_entry = (
        f"[AGENT TURN] timestamp='{timestamp}' session_id='{session_id}' "
        f"skill='{skill_used}' provider='{provider}' citations={citations_count} "
        f"prompt_length={len(prompt)}"
    )
    logger.info(log_entry)
