"""
FastAPI Application Entrypoint
Assembles routes, CORS middleware, lifespan events, and static frontend file serving.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import get_settings
from backend.app.db import init_db
from backend.app.logging_config import setup_logging
from backend.app.api import health, sessions, chat, artifacts
from ingestion.ingest import ingest_transcripts

# Initialize structured logging
logger = setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Initializing The Lenny Growth Assistant Application...")

    # Initialize Database Schema & pgvector
    try:
        await init_db()
        logger.info("Database schema initialized.")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    # Automatically run sample transcript ingestion if data directory exists
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ingestion", "data"))
    if os.path.exists(data_dir):
        try:
            logger.info("Checking transcript ingestion...")
            await ingest_transcripts(data_dir=data_dir, check_only=False)
        except Exception as e:
            logger.warning(f"Automatic transcript ingestion skipped or failed: {e}")

    yield

    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered Growth Strategy Assistant grounded on Lenny's Podcast transcripts.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(artifacts.router)

# Mount Frontend Static Directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend index.html not found"}
