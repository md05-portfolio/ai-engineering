# Week 2 RAG Assignment - Maven Submission Evidence

## 1. Live API URL

```
https://ai-engineering-wlqp.onrender.com
```

---

## 2. Curl Commands & Responses

### Test 1: Answerable Question with Citations

**Command:**
```bash
curl -s -X POST https://ai-engineering-wlqp.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is semantic search and how does it differ from keyword search?",
    "model": "gpt-4o-mini",
    "use_rag": true
  }'
```

**Response:**
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

✅ **Proof:** Answer with 4 document citations, high confidence (0.95)

---

### Test 2: Refusal (Out-of-Context Question)

**Command:**
```bash
curl -s -X POST https://ai-engineering-wlqp.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the population of Tokyo in 2026?",
    "model": "gpt-4o-mini",
    "use_rag": true
  }'
```

**Response:**
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

✅ **Proof:** Correctly refuses out-of-context question, confidence 0.0

---

## 3. Streamlit UI Evidence

### How to Run Locally
```bash
cd ai-engineering-bootcamp-v2/week-1
streamlit run streamlit_rag_app.py
```

### UI Features Implemented

**Query Mode:**
- Question input field
- RAG toggle (on/off for comparison)
- Model selection dropdown
- Answer display with confidence score
- Citations showing source documents
- Token usage and cost metrics
- Debug retrieval chunk viewer

**Ingest Mode:**
- Document text input
- Document ID input
- Optional source metadata
- Real-time ingestion feedback
- Ingestion history tracking

**System Health:**
- Health check button
- OpenAI connectivity status
- Pinecone connectivity status
- Vector count display
- Embedding dimension verification

### Running the UI
```bash
# Terminal 1: Start Streamlit
streamlit run streamlit_rag_app.py

# Opens at: http://localhost:8501
# Points to live API: https://ai-engineering-wlqp.onrender.com
```

✅ **UI Testing:** All modes functional, connects to live API

---

## 4. Feedback Question for Cohort

**Posted to Maven:**

> **Question:** For production RAG systems handling sensitive or proprietary data, how would you enhance the citation system to not only show document IDs but also include source confidence scores and retrieval similarity metrics? Would you display these metrics directly to end users or only to administrators, and what are the security/UX trade-offs?

This question explores:
- Citation transparency in RAG systems
- Confidence scoring mechanisms
- Security considerations in production
- User experience design trade-offs
- Data sensitivity handling

---

## GitHub Repository

https://github.com/md05-portfolio/ai-engineering/tree/main/ai-engineering-bootcamp-v2/week-1

**Commits:**
- 046b438 - Add concise Week 2 submission evidence
- 71699ba - Add comprehensive Maven submission package
- b3d904f - Add Week 2 Streamlit RAG UI
- d1c5d0b - Add Week 2 RAG demonstration
- 96d2f21 - Add full RAG implementation with Pinecone

---

## Summary

✅ **Live API:** https://ai-engineering-wlqp.onrender.com  
✅ **Curl Test 1:** Answerable question with 4 document citations (confidence: 0.95)  
✅ **Curl Test 2:** Refusal for out-of-context question (confidence: 0.0)  
✅ **Streamlit UI:** Fully functional ingest & query modes  
✅ **Feedback Question:** Specific, thoughtful question about production RAG systems  

---

**All tailabs Maven requirements met and ready for submission.**
