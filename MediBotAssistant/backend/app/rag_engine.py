"""
RAG Engine — loads all models once at startup and exposes:
- hybrid_search()
- rerank()
- rag_chain()
- sql_rag_chain()
"""

import re
import sqlite3
from groq import Groq
from qdrant_client import QdrantClient, models as qmodels
from sentence_transformers import SentenceTransformer, CrossEncoder
from fastembed import SparseTextEmbedding
from app.config import settings
from app.rbac.access_matrix import get_allowed_collections, can_use_sql_rag

# ─── Load models once at startup ────────────────────────
print("Loading RAG engine...")

qdrant = QdrantClient(path=settings.QDRANT_PATH)
print("✅ Qdrant loaded")

dense_model = SentenceTransformer(settings.DENSE_EMBEDDING_MODEL)
print("✅ Dense embedding model loaded")

sparse_model = SparseTextEmbedding(model_name=settings.SPARSE_EMBEDDING_MODEL)
print("✅ Sparse BM25 model loaded")

reranker = CrossEncoder(settings.RERANKER_MODEL)
print("✅ Cross-encoder reranker loaded")

groq_client = Groq(api_key=settings.GROQ_API_KEY)
print("✅ Groq client ready")

print("🚀 RAG engine ready!")


# ─── Hybrid Search with RBAC ────────────────────────────

def hybrid_search(query: str, role: str, top_k: int = None):
    """
    Hybrid dense + BM25 search with manual RBAC filtering.
    Restricted chunks are filtered BEFORE returning to caller —
    they never reach the LLM.
    """
    if top_k is None:
        top_k = settings.HYBRID_TOP_K

    dense_vec = dense_model.encode(query, normalize_embeddings=True).tolist()
    sparse_vec = list(sparse_model.embed([query]))[0]

    results = qdrant.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        prefetch=[
            qmodels.Prefetch(query=dense_vec, using="dense", limit=top_k * 3),
            qmodels.Prefetch(
                query=qmodels.SparseVector(
                    indices=sparse_vec.indices.tolist(),
                    values=sparse_vec.values.tolist(),
                ),
                using="sparse",
                limit=top_k * 3,
            ),
        ],
        query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
        limit=top_k * 3,
        with_payload=True,
    )

    # RBAC enforcement — role must be in chunk's access_roles
    filtered = [
        r for r in results.points
        if role in r.payload.get("access_roles", [])
    ]

    return filtered[:top_k]


# ─── Reranker ───────────────────────────────────────────

def rerank(query: str, chunks: list, top_k: int = None):
    """Rerank chunks using cross-encoder. Narrows top-10 to top-3."""
    if top_k is None:
        top_k = settings.RERANK_TOP_K

    if not chunks:
        return []

    pairs = [[query, chunk.payload["text"]] for chunk in chunks]
    scores = reranker.predict(pairs)
    scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


# ─── SQL RAG ────────────────────────────────────────────

def get_db_schema():
    conn = sqlite3.connect(settings.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    schema = []
    for (table,) in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        col_defs = ", ".join([f"{c[1]} ({c[2]})" for c in cols])
        cursor.execute(f"SELECT * FROM {table} LIMIT 2")
        samples = cursor.fetchall()
        schema.append(f"Table: {table}\nColumns: {col_defs}\nSample rows: {samples}")
    conn.close()
    return "\n\n".join(schema)


def extract_sql(raw_text: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"(SELECT\s+.+)", raw_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw_text.strip()


def sql_rag_chain(question: str, role: str) -> str:
    """3-step SQL RAG: question → SQL → execute → natural language answer."""
    if not can_use_sql_rag(role):
        return f"Access denied. SQL RAG is only available to billing_executive and admin roles."

    schema = get_db_schema()

    # Step 1: Translate to SQL
    sql_response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{
            "role": "user",
            "content": f"""You are a SQL expert. Write a SQL query to answer the question.
Return ONLY the SQL query, no explanation, no markdown fences.

Schema:
{schema}

Question: {question}
SQL:"""
        }],
        temperature=0,
    )
    sql_query = extract_sql(sql_response.choices[0].message.content)

    # Step 2: Execute SQL
    try:
        conn = sqlite3.connect(settings.SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        result_str = f"Columns: {columns}\nRows: {rows}"
    except Exception as e:
        return f"SQL execution error: {e}"

    # Step 3: Natural language answer
    answer_response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{
            "role": "user",
            "content": f"""You are a helpful medical assistant.
A user asked: "{question}"
The database returned: {result_str}
Give a clear, concise natural language answer."""
        }],
        temperature=0,
    )
    return answer_response.choices[0].message.content


# ─── Full RAG Chain ─────────────────────────────────────

def is_analytical_question(question: str) -> bool:
    keywords = [
        "how many", "count", "total", "sum", "average",
        "most", "least", "percentage", "statistics",
        "last month", "this month", "pending",
        "approved", "rejected", "escalated"
    ]
    return any(k in question.lower() for k in keywords)


def rag_chain(question: str, role: str) -> dict:
    """
    Main RAG chain:
    - Routes analytical questions to SQL RAG (if role permitted)
    - Routes document questions to Hybrid RAG + Rerank + LLM
    """
    allowed_collections = get_allowed_collections(role)

    # Route to SQL RAG
    if is_analytical_question(question) and can_use_sql_rag(role):
        answer = sql_rag_chain(question, role)
        return {
            "answer": answer,
            "sources": [],
            "retrieval_type": "sql_rag",
            "role": role,
        }

    # Hybrid RAG
    candidates = hybrid_search(question, role=role, top_k=settings.HYBRID_TOP_K)

    if not candidates:
        return {
            "answer": f"As a {role}, you have access to the {', '.join(allowed_collections)} collections. I couldn't find relevant information for your query in those collections.",
            "sources": [],
            "retrieval_type": "hybrid_rag",
            "role": role,
        }

    # Rerank
    reranked = rerank(question, candidates, top_k=settings.RERANK_TOP_K)

    # Build context
    context_parts = []
    sources = []
    for i, chunk in enumerate(reranked):
        p = chunk.payload
        context_parts.append(f"[{i+1}] {p['text']}")
        sources.append({
            "source_document": p["source_document"],
            "section_title": p["section_title"],
            "collection": p["collection"],
        })

    context = "\n\n".join(context_parts)

    # Generate answer
    response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{
            "role": "user",
            "content": f"""You are MediBot, an intelligent assistant for MediAssist Health Network.
Answer the question using ONLY the context provided. If context is insufficient, say so clearly.

Context:
{context}

Question: {question}
Answer:"""
        }],
        temperature=0,
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": sources,
        "retrieval_type": "hybrid_rag",
        "role": role,
    }
