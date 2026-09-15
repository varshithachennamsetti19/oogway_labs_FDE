"""
SQLAlchemy ORM Data Models
Defines Session, Message, TranscriptChunk, and Artifact entities.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector
    VectorType = Vector(384)
except Exception:
    VectorType = JSON

from backend.app.db import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="New Chat Session")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    provider_used = Column(String(50), nullable=True)
    model_used = Column(String(100), nullable=True)
    citations = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")
    artifacts = relationship("Artifact", back_populates="message", cascade="all, delete-orphan")


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_title = Column(String(255), nullable=False)
    guest = Column(String(100), nullable=False)
    episode_url = Column(String(500), nullable=True)
    start_timestamp = Column(String(20), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(VectorType, nullable=True)  # 384-dimensional vector embedding
    metadata_json = Column(JSON, nullable=True, default=dict)


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True)
    artifact_type = Column(String(20), nullable=False, default="html")  # html | markdown
    title = Column(String(255), nullable=False, default="Generated Artifact")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="artifacts")
