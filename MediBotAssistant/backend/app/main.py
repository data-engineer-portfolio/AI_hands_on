"""
MediBot FastAPI Backend
=======================
Endpoints:
  POST /login                  — authenticate and get JWT token
  POST /chat                   — main RAG endpoint
  GET  /collections/{role}     — list accessible collections for a role
  GET  /health                 — health check
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    LoginRequest, LoginResponse,
    ChatRequest, ChatResponse, Source,
    CollectionsResponse, HealthResponse,
)
from app.auth import authenticate_user, create_access_token, decode_token
from app.rbac.access_matrix import get_allowed_collections, VALID_ROLES
from app.rag_engine import rag_chain

# ─── App ────────────────────────────────────────────────

app = FastAPI(
    title="MediBot API",
    description="AI-powered medical assistant with role-based access control",
    version="1.0.0",
)

# Allow Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ─────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "message": "MediBot API is running"}


# ─── Login ──────────────────────────────────────────────

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"],
    }


# ─── Collections ────────────────────────────────────────

@app.get("/collections/{role}", response_model=CollectionsResponse)
def get_collections(role: str):
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role: {role}. Valid roles: {VALID_ROLES}",
        )
    return {
        "role": role,
        "collections": get_allowed_collections(role),
    }


# ─── Chat ───────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Verify JWT and extract role
    token_data = decode_token(request.token)
    role = token_data["role"]

    # Run RAG chain (RBAC enforced inside rag_chain)
    result = rag_chain(request.question, role)

    return {
        "answer": result["answer"],
        "sources": [Source(**s) for s in result["sources"]],
        "retrieval_type": result["retrieval_type"],
        "role": role,
    }
