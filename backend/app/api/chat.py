"""
Chat & Agent Dispatch API Endpoint
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.agent.router import get_agent_router
from backend.app.db import get_db_session
from backend.app.models import Session as DBSession, Message as DBMessage, Artifact as DBArtifact
from backend.app.schemas import ChatRequest, ChatResponse, MessageResponse, ArtifactResponse

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_turn(payload: ChatRequest, db: AsyncSession = Depends(get_db_session)):
    """Receives a user message, executes agent router, and persists turn history."""

    # 1. Verify Session
    result = await db.execute(select(DBSession).where(DBSession.id == payload.session_id))
    session_obj = result.scalar_one_or_none()

    if not session_obj:
        # Auto-create session if missing
        session_obj = DBSession(id=payload.session_id, title=f"Chat: {payload.message[:30]}")
        db.add(session_obj)
        await db.flush()

    # 2. Persist User Message
    user_msg = DBMessage(
        session_id=session_obj.id,
        role="user",
        content=payload.message
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # Update session title if first message
    if session_obj.title == "New Growth Chat" or session_obj.title == "New Chat Session":
        session_obj.title = payload.message[:35] + ("..." if len(payload.message) > 35 else "")

    session_obj.updated_at = datetime.utcnow()

    # 3. Execute Agent Router
    router_engine = get_agent_router()
    agent_output = await router_engine.route_and_execute(
        session_id=session_obj.id,
        user_message=payload.message,
        provider_override=payload.provider_override,
        db=db
    )

    # 4. Persist Assistant Message & Artifact
    assistant_msg = DBMessage(
        session_id=session_obj.id,
        role="assistant",
        content=agent_output["answer"],
        provider_used=agent_output.get("provider_used"),
        model_used=agent_output.get("model_used"),
        citations=agent_output.get("citations", [])
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    artifact_obj = None
    artifact_payload = agent_output.get("artifact")
    if artifact_payload:
        db_artifact = DBArtifact(
            id=artifact_payload["id"],
            message_id=assistant_msg.id,
            artifact_type=artifact_payload["artifact_type"],
            title=artifact_payload["title"],
            content=artifact_payload["content"]
        )
        db.add(db_artifact)
        await db.commit()
        await db.refresh(db_artifact)
        artifact_obj = ArtifactResponse.model_validate(db_artifact)

    user_msg_response = MessageResponse(
        id=user_msg.id,
        session_id=user_msg.session_id,
        role=user_msg.role,
        content=user_msg.content,
        provider_used=user_msg.provider_used,
        model_used=user_msg.model_used,
        citations=user_msg.citations or [],
        artifacts=[],
        created_at=user_msg.created_at
    )

    assistant_msg_response = MessageResponse(
        id=assistant_msg.id,
        session_id=assistant_msg.session_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        provider_used=assistant_msg.provider_used,
        model_used=assistant_msg.model_used,
        citations=assistant_msg.citations or [],
        artifacts=[artifact_obj] if artifact_obj else [],
        created_at=assistant_msg.created_at
    )

    return ChatResponse(
        session_id=session_obj.id,
        user_message=user_msg_response,
        assistant_message=assistant_msg_response,
        skill_used=agent_output.get("skill_name", "rag_skill"),
        artifact=artifact_obj
    )
