"""
Central configuration loaded from environment variables (.env file).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    # Qdrant (local mode - path based, no server needed)
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", "./qdrant_data")

    # SQLite
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "../data/mediassist.db")

    # Embeddings
    DENSE_EMBEDDING_MODEL: str = os.getenv("DENSE_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    SPARSE_EMBEDDING_MODEL: str = os.getenv("SPARSE_EMBEDDING_MODEL", "Qdrant/bm25")

    # Reranker
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev_secret_change_me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))

    # Qdrant collection name (single collection, filtered by metadata)
    QDRANT_COLLECTION_NAME: str = "medibot_chunks"

    # Retrieval tuning
    HYBRID_TOP_K: int = 10   # initial candidate set size
    RERANK_TOP_K: int = 3    # final chunks passed to LLM


settings = Settings()
