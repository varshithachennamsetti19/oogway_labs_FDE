"""
Pydantic API Schemas & Serialization Contracts
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


# --- Health Schemas ---
class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str
    version: str = "1.0.0"


class DBHealthResponse(BaseModel):
    status: str
    database: str
    pgvector_enabled: bool
    total_transcript_chunks: int


class LLMHealthResponse(BaseModel):
    status: str
    active_provider: str
    active_model: str
    available_providers: List[str]
    ollama_status: str


# --- Citation & Artifact Schemas ---
class Citation(BaseModel):
    episode_title: str
    guest: str
    episode_url: Optional[str] = None
    start_timestamp: Optional[str] = None
    snippet: str
    similarity_score: float


class ArtifactResponse(BaseModel):
    id: str
    artifact_type: str  # html | markdown
    title: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Message & Session Schemas ---
class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    citations: Optional[List[Citation]] = []
    artifacts: Optional[List[ArtifactResponse]] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionCreate(BaseModel):
    title: Optional[str] = "New Growth Chat"


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse] = []



# --- Chat Request & Response ---
class ChatRequest(BaseModel):
    session_id: str
    message: str
    provider_override: Optional[str] = None  # anthropic | openai | ollama


class ChatResponse(BaseModel):
    session_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    skill_used: str
    artifact: Optional[ArtifactResponse] = None
