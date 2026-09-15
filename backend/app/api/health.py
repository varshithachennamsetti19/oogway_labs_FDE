"""
Health Diagnostic Endpoints
Implements /health, /health/db, and /health/llm for operational monitoring.
"""

from datetime import datetime
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.db import get_db_session
from backend.app.models import TranscriptChunk
from backend.app.schemas import HealthResponse, DBHealthResponse, LLMHealthResponse

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Main application operational health check."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.VERSION
    )


@router.get("/health/db", response_model=DBHealthResponse)
async def db_health_check(db: AsyncSession = Depends(get_db_session)):
    """Database and pgvector connectivity health check."""
    try:
        # Query total transcript chunks
        result = await db.execute(select(func.count()).select_from(TranscriptChunk))
        count = result.scalar() or 0

        # Check pgvector
        pgvector_enabled = True
        try:
            await db.execute(text("SELECT '[1,2,3]'::vector;"))
        except Exception:
            pgvector_enabled = False

        return DBHealthResponse(
            status="ok",
            database="postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite",
            pgvector_enabled=pgvector_enabled,
            total_transcript_chunks=count
        )
    except Exception as e:
        return DBHealthResponse(
            status=f"error: {str(e)}",
            database="unknown",
            pgvector_enabled=False,
            total_transcript_chunks=0
        )


@router.get("/health/llm", response_model=LLMHealthResponse)
async def llm_health_check():
    """LLM Providers status health check."""
    available_providers = []

    if settings.ANTHROPIC_API_KEY and "your_anthropic" not in settings.ANTHROPIC_API_KEY:
        available_providers.append("anthropic")

    if settings.OPENAI_API_KEY and "your_openai" not in settings.OPENAI_API_KEY:
        available_providers.append("openai")

    # Check Ollama
    ollama_status = "unavailable"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            if res.status_code == 200:
                ollama_status = "ready"
                available_providers.append("ollama")
    except Exception:
        ollama_status = "offline"

    # Always add offline fallback provider
    available_providers.append("offline_fallback")

    return LLMHealthResponse(
        status="ok",
        active_provider=settings.DEFAULT_LLM_PROVIDER,
        active_model=settings.ANTHROPIC_MODEL if settings.DEFAULT_LLM_PROVIDER == "anthropic" else settings.OLLAMA_MODEL,
        available_providers=available_providers,
        ollama_status=ollama_status
    )
