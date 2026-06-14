"""
Pydantic request/response schemas for all FastAPI endpoints.
"""

from pydantic import BaseModel
from typing import List, Optional


# ─── Auth ───────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


# ─── Chat ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    token: str  # JWT token from /login

class Source(BaseModel):
    source_document: str
    section_title: str
    collection: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    retrieval_type: str  # "hybrid_rag" or "sql_rag"
    role: str


# ─── Collections ────────────────────────────────────────

class CollectionsResponse(BaseModel):
    role: str
    collections: List[str]


# ─── Health ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    message: str
