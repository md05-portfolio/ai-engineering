# Week 2 RAG Assignment - Submission Evidence

**Live API URL:** https://ai-engineering-wlqp.onrender.com

---

## Evidence 1: Question Answerable from Ingested Documents

### Curl Command
```bash
curl -s -X POST https://ai-engineering-wlqp.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is semantic search and how does it differ from keyword search?",
    "model": "gpt-4o-mini",
    "use_rag": true
  }'
```

### JSON Response
```json
{
    "answer": {
        "answer": "Semantic search finds relevant documents based on meaning rather than keyword matching. It involves converting queries and documents to embeddings, computing similarity between these embeddings using metrics like cosine similarity or Euclidean distance, and then ranking and returning the top-k most similar results. Unlike keyword search, which relies on exact word matches, semantic search excels at understanding intent and synonyms, allowing it to retrieve documents based on the underlying meaning of the search terms. For example, searching for 'fast cars' can yield results about 'rapid automobiles' even without exact keyword overlap.",
        "confidence": 0.95,
        "sources_needed": false
    },
    "tokens_used": 755,
    "model": "gpt-4o-mini",
    "latency_ms": 1715,
    "cost_usd": 0.000168,
    "citations": [
        "embeddings-guide-002",
        "semantic-search-005",
        "vector-db-001",
        "rag-fundamentals-001"
    ],
    "retrieved_chunks": 4
}
```

✅ **Proof:** Answer provided with 4 document citations, confidence 0.95, tokens and cost tracked.

---

## Evidence 2: Question NOT in Documents (Refusal)

### Curl Command
```bash
curl -s -X POST https://ai-engineering-wlqp.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the population of Tokyo in 2026?",
    "model": "gpt-4o-mini",
    "use_rag": true
  }'
```

### JSON Response
```json
{
    "answer": {
        "answer": "I don't have enough information to answer that question based on the available documents.",
        "confidence": 0.0,
        "sources_needed": false
    },
    "tokens_used": 476,
    "model": "gpt-4o-mini",
    "latency_ms": 942,
    "cost_usd": 8.4e-05,
    "citations": [
        "rag-intro-001",
        "rag-fundamentals-001",
        "vector-db-001",
        "llm-prompting-004",
        "vector-db-overview-003"
    ],
    "retrieved_chunks": 5
}
```

✅ **Proof:** Refusal triggered correctly, confidence 0.0, no hallucination, cost tracked.

---

## GitHub Repository

https://github.com/md05-portfolio/ai-engineering/tree/main/ai-engineering-bootcamp-v2/week-1

**Key Files:**
- `main.py` - RAG-enhanced FastAPI backend
- `batch_ingest.py` - Batch document ingestion
- `streamlit_rag_app.py` - Interactive UI
- `requirements.txt` - Dependencies with Pinecone + langchain-text-splitters
