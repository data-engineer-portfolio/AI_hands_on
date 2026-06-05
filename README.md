# 🛡️ Insurance RAG Pipeline — ChromaDB + Groq

A Retrieval-Augmented Generation (RAG) pipeline built for insurance domain Q&A. Ask questions about policies, claims, underwriting, and regulations — and get grounded, accurate answers powered by a vector search over a curated insurance knowledge base.

---

## 📌 What This Project Does

Instead of relying on an LLM's general knowledge, this pipeline:

1. Loads an insurance knowledge base (`.txt`)
2. Splits it into chunks and converts them into vector embeddings
3. Stores embeddings in **ChromaDB** (a local vector database)
4. When a question is asked, retrieves the most relevant chunks
5. Sends those chunks as context to **Groq LLM** to generate a grounded answer

> Think of it as giving the LLM an open-book exam — it looks up the relevant pages first, then answers.

---

## 🏗️ Pipeline Architecture

```
insurance_rag_knowledge_base.txt
           │
           ▼
   ┌───────────────┐
   │   Chunking    │  50-word chunks
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │  Embeddings   │  all-MiniLM-L6-v2 → 384-dim vectors
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │   ChromaDB    │  Persistent local vector store
   └───────┬───────┘
           │
      User Query
           │
           ▼
   ┌───────────────┐
   │   Retrieval   │  Top-k similarity search
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │   Groq LLM    │  Grounded answer generation
   └───────────────┘
```

---

## 🧰 Tech Stack

| Component | Tool | Purpose |
|---|---|---|
| Vector Database | `ChromaDB` | Store and search embeddings locally |
| Embedding Model | `all-MiniLM-L6-v2` | Convert text to 384-dim vectors |
| LLM | `Groq (LLaMA3)` | Generate answers from retrieved context |
| Text Splitting | Custom word chunker | Break documents into manageable pieces |
| Environment | Google Colab | Notebook execution |

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install chromadb sentence-transformers langchain_text_splitters pypdf groq
```

### 2. Set Your Groq API Key

Get a free API key from [console.groq.com](https://console.groq.com)

```python
import os
os.environ["GROQ_API_KEY"] = "your_groq_api_key_here"
```

### 3. Run the Notebook

Open `Vector_chromaDB_rag_pipeline.ipynb` in Google Colab and run all cells top to bottom.

---

## 💬 Example Queries

```python
answer, context = rag("What happens if my insurance claim is denied?")
answer, context = rag("What is the difference between term and whole life insurance?")
answer, context = rag("How does subrogation work?")
answer, context = rag("What factors affect my auto insurance premium?")
answer, context = rag("What does homeowners insurance typically cover?")
```

---

## 📁 Project Structure

```
📦 insurance-rag-pipeline
 ┣ 📓 Vector_chromaDB_rag_pipeline.ipynb   # Main notebook
 ┣ 📄 insurance_rag_knowledge_base.txt     # Insurance knowledge base
 ┣ 📁 tmp/chromadb/                        # ChromaDB persistent storage (auto-created)
 ┗ 📄 README.md                            # This file
```

---

## 🧠 Key Concepts

**RAG (Retrieval-Augmented Generation)**
Combines a retrieval system (ChromaDB) with a generative model (Groq LLM). The retriever finds relevant document chunks; the LLM generates answers grounded in those chunks — reducing hallucination.

**Vector Embeddings**
Text is converted into numerical vectors (384 numbers) that capture semantic meaning. Similar sentences produce similar vectors, enabling meaning-based search rather than keyword matching.

**ChromaDB**
A lightweight, open-source vector database that runs locally. It stores embeddings and performs fast similarity search using cosine or L2 distance.

**Groq**
A high-speed LLM inference platform. This pipeline uses `llama3-8b-8192` for fast, accurate response generation.

---

## ⚙️ Configuration

| Parameter | Default | Description |
|---|---|---|
| `chunk_size` | `50` | Words per chunk |
| `top_k` | `5` | Number of chunks retrieved per query |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `GROQ_MODEL` | `llama3-8b-8192` | Groq LLM model |
| `temperature` | `0.2` | LLM creativity (lower = more factual) |

---

## ⚠️ Known Limitations

- Chunk size of 50 words is small — sentences may be cut mid-thought. Consider increasing to 150–300 words with overlap for better retrieval.
- No chunk overlap — context at boundaries can be lost.
- Knowledge base is static — does not update in real time.

---

## 📚 Knowledge Base Coverage

The insurance knowledge base covers:

- 📋 Types of Insurance Policies (Life, Health, Auto, Property, Liability, Specialty)
- 📝 Claims Process (step-by-step, fraud, disputes, subrogation)
- 🔍 Underwriting (risk assessment, pricing, policy issuance)
- 📖 Policy Terms & Conditions (deductibles, exclusions, endorsements)
- ⚖️ Regulations & Compliance (ACA, state regulation, consumer protections)
- 💰 Premium Factors & Discounts
- 📚 Insurance Glossary (40+ terms)

---

## 🙌 Acknowledgements

- [ChromaDB](https://www.trychroma.com/) — vector database
- [Sentence Transformers](https://www.sbert.net/) — embedding model
- [Groq](https://groq.com/) — LLM inference
- [LLaMA 3](https://ai.meta.com/llama/) — base language model by Meta

---

## 📜 License

This project is for educational and portfolio purposes.
