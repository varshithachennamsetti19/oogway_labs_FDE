"""
Artifact Retrieval API Endpoint
Serves artifact payloads for sandboxed rendering.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db import get_db_session
from backend.app.models import Artifact as DBArtifact
from backend.app.schemas import ArtifactResponse

router = APIRouter(prefix="/api/artifacts", tags=["Artifacts"])


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str, db: AsyncSession = Depends(get_db_session)):
    """Retrieves artifact record by ID."""
    result = await db.execute(select(DBArtifact).where(DBArtifact.id == artifact_id))
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")

    return ArtifactResponse.model_validate(artifact)


@router.get("/{artifact_id}/raw", response_class=HTMLResponse)
async def get_artifact_raw_html(artifact_id: str, db: AsyncSession = Depends(get_db_session)):
    """Serves raw HTML payload with injected Content Security Policy."""
    result = await db.execute(select(DBArtifact).where(DBArtifact.id == artifact_id))
    artifact = result.scalar_one_or_none()

    if not artifact:
        return HTMLResponse("<h3>Artifact Not Found</h3>", status_code=404)

    return HTMLResponse(content=artifact.content, status_code=200)
