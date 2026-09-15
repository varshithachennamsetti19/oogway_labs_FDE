"""
Session Management API Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.app.db import get_db_session
from backend.app.models import Session as DBSession, Message as DBMessage
from backend.app.schemas import SessionCreate, SessionResponse, SessionDetailResponse, MessageResponse

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db_session)):
    """Retrieves list of active chat sessions."""
    result = await db.execute(
        select(DBSession).order_by(DBSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    response = []
    for s in sessions:
        # Count messages
        msg_count_res = await db.execute(
            select(func.count()).select_from(DBMessage).where(DBMessage.session_id == s.id)
        )
        msg_count = msg_count_res.scalar() or 0
        response.append(SessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=msg_count
        ))

    return response


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db_session)):
    """Creates a new chat session."""
    session_title = payload.title or "New Growth Chat"
    new_session = DBSession(title=session_title)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return SessionResponse(
        id=new_session.id,
        title=new_session.title,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
        message_count=0
    )


@router.get("/{session_id}/messages", response_model=SessionDetailResponse)
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db_session)):
    """Retrieves a session and all its messages with citations and artifacts."""
    result = await db.execute(
        select(DBSession)
        .options(selectinload(DBSession.messages).selectinload(DBMessage.artifacts))
        .where(DBSession.id == session_id)
    )
    session_obj = result.scalar_one_or_none()

    if not session_obj:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return SessionDetailResponse(
        id=session_obj.id,
        title=session_obj.title,
        created_at=session_obj.created_at,
        updated_at=session_obj.updated_at,
        message_count=len(session_obj.messages),
        messages=[
            MessageResponse.model_validate(msg) for msg in session_obj.messages
        ]
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db_session)):
    """Deletes a chat session and its history."""
    result = await db.execute(select(DBSession).where(DBSession.id == session_id))
    session_obj = result.scalar_one_or_none()

    if not session_obj:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    await db.delete(session_obj)
    await db.commit()
    return None
