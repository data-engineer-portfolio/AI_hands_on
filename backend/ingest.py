"""
Standalone ingestion script.
Run once to parse PDFs and index into local Qdrant.
Usage: python ingest.py
"""

import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from qdrant_client import QdrantClient, models as qmodels
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from docling.document_converter import DocumentConverter
import torch
from docling_core.transforms.chunker import HybridChunker

# ─── Config ─────────────────────────────────────────────
QDRANT_PATH     = os.getenv("QDRANT_PATH", "./qdrant_data")
COLLECTION_NAME = "medibot_chunks"
DATA_BASE       = os.getenv("DATA_BASE_PATH", "../data/raw")
DENSE_MODEL     = os.getenv("DENSE_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
SPARSE_MODEL    = os.getenv("SPARSE_EMBEDDING_MODEL", "Qdrant/bm25")

# RBAC mapping: collection → roles that can access it
COLLECTION_ROLES = {
    "general":  ["doctor", "nurse", "billing_executive", "technician", "admin"],
    "clinical": ["doctor", "admin"],
    "nursing":  ["doctor", "nurse", "admin"],
    "billing":  ["billing_executive", "admin"],
    "equipment":["technician", "admin"],
}

DATA_DIRS = {
    col: os.path.join(DATA_BASE, col)
    for col in COLLECTION_ROLES
}

# ─── Init ───────────────────────────────────────────────
print("Initializing models...")
client       = QdrantClient(path=QDRANT_PATH)
dense_model  = SentenceTransformer(DENSE_MODEL)
sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL)
converter    = DocumentConverter()
chunker      = HybridChunker(max_tokens=256)
DENSE_DIM    = dense_model.get_sentence_embedding_dimension()
print(f"✅ Models loaded — dense dim: {DENSE_DIM}")

# ─── Recreate collection ─────────────────────────────────
if client.collection_exists(COLLECTION_NAME):
    client.delete_collection(COLLECTION_NAME)
    print("🗑️  Deleted existing collection")

client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config={
        "dense": qmodels.VectorParams(size=DENSE_DIM, distance=qmodels.Distance.COSINE)
    },
    sparse_vectors_config={
        "sparse": qmodels.SparseVectorParams(
            index=qmodels.SparseIndexParams(on_disk=False)
        )
    }
)
print(f"✅ Collection '{COLLECTION_NAME}' created")

# ─── Parse + Chunk ──────────────────────────────────────
all_chunks = []

for collection, dir_path in DATA_DIRS.items():
    if not os.path.exists(dir_path):
        print(f"⚠️  Skipping {collection} — folder not found: {dir_path}")
        continue

    print(f"\n📂 Processing: {collection}")
    access_roles = COLLECTION_ROLES[collection]

    for file in Path(dir_path).iterdir():
        if file.suffix.lower() not in [".pdf", ".md"]:
            continue

        print(f"  📄 Parsing: {file.name} ...", end=" ")
        try:
            result = converter.convert(str(file))
            chunks = list(chunker.chunk(result.document))

            for chunk in chunks:
                text = chunk.text.strip() if chunk.text else ""
                if not text:
                    continue

                headings = []
                if hasattr(chunk, "meta") and chunk.meta:
                    if hasattr(chunk.meta, "headings") and chunk.meta.headings:
                        headings = chunk.meta.headings

                section_title = headings[-1] if headings else "General"

                if "|" in text and text.count("|") > 3:
                    chunk_type = "table"
                elif len(text.split()) < 8:
                    chunk_type = "heading"
                else:
                    chunk_type = "text"

                enriched = f"{section_title}\n{text}" if section_title != "General" else text

                all_chunks.append({
                    "text": enriched,
                    "source_document": file.name,
                    "collection": collection,
                    "access_roles": access_roles,
                    "section_title": section_title,
                    "chunk_type": chunk_type,
                })

            print(f"→ {len(chunks)} chunks")
        except Exception as e:
            print(f"❌ Error: {e}")

print(f"\n✅ Total chunks: {len(all_chunks)}")

# ─── Index ──────────────────────────────────────────────
print("\n📥 Indexing into Qdrant...")
BATCH = 32

for i in range(0, len(all_chunks), BATCH):
    batch = all_chunks[i:i+BATCH]
    texts = [c["text"] for c in batch]

    dense_vecs  = dense_model.encode(texts, normalize_embeddings=True).tolist()
    sparse_vecs = list(sparse_model.embed(texts))

    points = []
    for j, chunk in enumerate(batch):
        sv = sparse_vecs[j]
        points.append(qmodels.PointStruct(
            id=str(uuid.uuid4()),
            vector={
                "dense": dense_vecs[j],
                "sparse": qmodels.SparseVector(
                    indices=sv.indices.tolist(),
                    values=sv.values.tolist(),
                )
            },
            payload={
                "text":            chunk["text"],
                "source_document": chunk["source_document"],
                "collection":      chunk["collection"],
                "access_roles":    chunk["access_roles"],
                "section_title":   chunk["section_title"],
                "chunk_type":      chunk["chunk_type"],
            }
        ))

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"  Indexed {min(i+BATCH, len(all_chunks))}/{len(all_chunks)} chunks...")

info = client.get_collection(COLLECTION_NAME)
print(f"\n✅ Done! {info.points_count} points stored in Qdrant.")
