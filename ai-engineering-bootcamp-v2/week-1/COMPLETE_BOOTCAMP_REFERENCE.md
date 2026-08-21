# Complete AI Bootcamp Reference (Weeks 1-3)

**Status:** All weeks implemented  
**Last Updated:** August 13, 2026  
**GitHub:** https://github.com/md05-portfolio/ai-engineering/tree/main/ai-engineering-bootcamp-v2/week-1

---

# 🎓 Bootcamp Overview

| Week | Focus | Pattern | Status |
|------|-------|---------|--------|
| **Week 1** | Basic AI Endpoint | Linear (Ask → Answer) | ✅ Complete |
| **Week 2** | Retrieval-Augmented Generation | Linear with Context (Search → Ground → Answer) | ✅ Complete |
| **Week 3** | Agentic AI | Loop (Think → Act → Observe → Decide) | 🔨 In Progress |

---

# WEEK 1: Basic AI Endpoint

## What It Does
Simple API that answers questions using OpenAI's language model.

**Simple Explanation:** A robot that answers questions from its training knowledge.

## Architecture

```
User Question
    ↓
OpenAI Chat Completion API
    ↓
Structured Output (Answer object)
    ↓
Return: answer + tokens_used + cost_usd
```

## Endpoints

### `POST /ask`
**Request:**
```json
{
  "question": "What is RAG?",
  "model": "gpt-4o-mini",
  "use_rag": false
}
```

**Response:**
```json
{
  "answer": {
    "answer": "RAG is...",
    "confidence": 0.95,
    "sources_needed": false
  },
  "tokens_used": 145,
  "model": "gpt-4o-mini",
  "latency_ms": 450,
  "cost_usd": 0.000043
}
```

### `GET /health`
**Response:**
```json
{
  "status": "ok",
  "openai": "connected"
}
```

## Key Code Components

**File:** `main.py`

```python
def call_model_structured(question: str, model: str) -> tuple[Answer, int, int, int]:
    """Generate answer using OpenAI structured output."""
    completion = client.chat.completions.parse(
        model=model,
        messages=[{"role": "user", "content": question}],
        response_format=Answer,
    )
    return parsed, total_tokens, prompt_tokens, completion_tokens

@app.post("/ask")
def ask(body: AskRequest) -> AskResponse:
    """Answer questions with token tracking and cost calculation."""
    answer, tokens, prompt_t, completion_t = call_model_structured(body.question, model)
    cost = compute_cost_usd(model, prompt_t, completion_t)
    return AskResponse(..., tokens_used=tokens, cost_usd=cost)
```

## Pydantic Models

```python
class Answer(BaseModel):
    answer: str
    confidence: float
    sources_needed: bool

class AskRequest(BaseModel):
    question: str
    model: str | None = None

class AskResponse(BaseModel):
    answer: Answer
    tokens_used: int
    model: str
    latency_ms: int
    cost_usd: float
```

## Deployment
- **Live URL:** https://ai-engineering-wlqp.onrender.com
- **Endpoint:** `POST https://ai-engineering-wlqp.onrender.com/ask`

## Test Command
```bash
curl -X POST https://ai-engineering-wlqp.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?", "use_rag": false}'
```

---

# WEEK 2: Retrieval-Augmented Generation

## What It Does
Enhanced API that retrieves documents, grounds LLM responses in context, and cites sources.

**Simple Explanation:** A robot with a library of books. It reads the books before answering, cites which books it used, and refuses to answer if books don't cover the topic.

## Architecture

```
User Question
    ↓
Embed question (text-embedding-3-small)
    ↓
Retrieve top-5 chunks from Pinecone
    ↓
Ground LLM with context ("Answer using ONLY this context")
    ↓
LLM generates answer with citations
    ↓
Return: answer + citations + retrieved_chunks + cost_usd
```

## Endpoints

### `POST /ingest` (New in Week 2)
**Request:**
```json
{
  "text": "Semantic search finds documents based on meaning...",
  "document_id": "semantic-search-005",
  "metadata": {"source": "tutorial.md"}
}
```

**Response:**
```json
{
  "document_id": "semantic-search-005",
  "chunks_indexed": 2,
  "status": "success"
}
```

### `GET /debug/retrieve` (New in Week 2)
**Request:**
```
GET /debug/retrieve?q=what+is+semantic+search
```

**Response:**
```json
[
  {
    "chunk_id": "semantic-search-005#0",
    "text": "Semantic search finds relevant documents...",
    "similarity_score": 0.61,
    "metadata": {"document_id": "semantic-search-005"}
  },
  ...
]
```

### `POST /ask` (Enhanced in Week 2)
**Request:**
```json
{
  "question": "What is semantic search?",
  "model": "gpt-4o-mini",
  "use_rag": true
}
```

**Response:**
```json
{
  "answer": {
    "answer": "Semantic search finds documents based on meaning...",
    "confidence": 0.95,
    "sources_needed": false
  },
  "tokens_used": 755,
  "model": "gpt-4o-mini",
  "latency_ms": 1715,
  "cost_usd": 0.000168,
  "citations": ["semantic-search-005", "vector-db-001", "embeddings-guide-002"],
  "retrieved_chunks": 3
}
```

## Key Components

### Vector Store
- **Provider:** Pinecone
- **Index Name:** `ai-engineer-rag`
- **Embedding Model:** `text-embedding-3-small` (1536 dimensions)
- **Total Vectors:** 12 (from 5 documents, 9 chunks)

### Chunking Strategy
```python
RecursiveCharacterTextSplitter(
    chunk_size=800,      # 800 characters per chunk
    chunk_overlap=100,   # 100 char overlap between chunks
    separators=["\n\n", "\n", ".", " ", ""]
)
```

### Embedding Process
```python
def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding  # 1536-dim vector
```

### Retrieval
```python
def retrieve_context(question: str, top_k: int = 5):
    query_embedding = embed_text(question)
    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True,
    )
    # Returns top-5 most similar chunks
```

### Grounding Prompt
```python
context_prompt = (
    "Answer using ONLY the context below. "
    "If context doesn't contain the answer, state: "
    "'I don't have enough information to answer that.'"
)
```

## Ingested Documents

| Doc ID | Title | Chunks | Topics |
|--------|-------|--------|--------|
| rag-fundamentals-001 | RAG Fundamentals | 2 | RAG concepts, retrieval |
| embeddings-guide-002 | Embeddings Guide | 1 | Vector representations |
| vector-db-overview-003 | Vector Databases | 2 | Pinecone, Weaviate |
| llm-prompting-004 | LLM Prompting | 2 | Prompting techniques |
| semantic-search-005 | Semantic Search | 2 | Similarity search |

**Total:** 5 documents → 9 chunks → 12 vectors (including Week 1 tests)

## Key Code

```python
def retrieve_context(question: str, top_k: int = 5) -> tuple[str, list[str]]:
    """Retrieve context + citations."""
    query_embedding = embed_text(question)
    results = index.query(vector=query_embedding, top_k=top_k)
    
    context_pieces = []
    cited_docs = set()
    for match in results.matches:
        metadata = match.metadata
        text = metadata.get("text", "")
        doc_id = metadata.get("document_id", "unknown")
        context_pieces.append(f"[{doc_id}] {text}")
        cited_docs.add(doc_id)
    
    return "\n\n".join(context_pieces), list(cited_docs)

@app.post("/ask")
def ask(body: AskRequest) -> AskResponse:
    if body.use_rag and pinecone_client:
        context, citations = retrieve_context(body.question, top_k=5)
        answer, tokens, prompt_t, completion_t = call_model_structured(
            body.question, 
            body.model,
            context=context
        )
        return AskResponse(
            answer=answer,
            tokens_used=tokens,
            citations=citations,
            retrieved_chunks=len(citations),
            cost_usd=compute_cost_usd(body.model, prompt_t, completion_t),
        )
    else:
        # Non-RAG mode (like Week 1)
        answer, tokens, prompt_t, completion_t = call_model_structured(body.question, body.model)
        return AskResponse(answer=answer, tokens_used=tokens, citations=None)
```

## Environment Variables
```
OPENAI_API_KEY=sk-proj-...
PINECONE_API_KEY=pcsk_6c9aRs_...
PINECONE_INDEX_NAME=ai-engineer-rag
PINECONE_ENVIRONMENT=us-east-1
```

## Deployment
- **Live API:** https://ai-engineering-wlqp.onrender.com
- **Live UI:** https://ai-engineering-streamlit.onrender.com

## Test Commands

**Answerable Question:**
```bash
curl -X POST https://ai-engineering-wlqp.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is semantic search?", "use_rag": true}'
# Returns: Citations, high confidence (0.95)
```

**Refusal (Out-of-context):**
```bash
curl -X POST https://ai-engineering-wlqp.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Tokyo population?", "use_rag": true}'
# Returns: "I don't have enough information...", confidence 0.0
```

---

# WEEK 3: Agentic AI

## What It Does
Agent that thinks, acts (calls tools), observes results, and decides next steps in a loop.

**Simple Explanation:** A robot that doesn't just answer—it plans multiple steps, searches for info, analyzes what it finds, and decides if it needs to search again or if it has enough to answer.

## Architecture

```
User Question
    ↓
[THINK] Agent plans next action
    ↓
[ACT] Calls tool (retrieve_documents)
    ↓
[OBSERVE] Receives tool results
    ↓
Decision: Answer or loop?
    ↓
If loop: back to THINK
If done: return final answer
```

## Decisions Locked

| Choice | Selection |
|--------|-----------|
| **Task** | Research-assistant (reuse Week 2 docs) |
| **Tool** | `/debug/retrieve` from Week 2 |
| **Stack** | Google ADK (genai library) |
| **Deployment** | Full Render |

## Job Definition (REQUIRED)

**"When a user asks a research question, the agent should find relevant documents via retrieval, analyze them, and then decide if it needs to search for more specific information or can answer based on what it found."**

**Why it's an agent:** Next step depends on unpredictable tool results (retrieval might find info or not).

## Implementation Files

### 1. Agent Code (`agent_research.py`)

```python
import google.genai as genai
from google.genai import Client
import os
from dotenv import load_dotenv
import httpx
import json

load_dotenv()
client = Client(api_key=os.getenv("GOOGLE_API_KEY"))

def retrieve_documents(query: str, top_k: int = 5) -> dict:
    """Search documents using Week 2 retrieval."""
    api_url = os.getenv("RAG_API_URL", "https://ai-engineering-wlqp.onrender.com")
    try:
        response = httpx.get(
            f"{api_url}/debug/retrieve",
            params={"q": query},
            timeout=10.0,
        )
        response.raise_for_status()
        return {"status": "success", "results": response.json(), "query": query}
    except Exception as e:
        return {"status": "error", "error": str(e)}

tools = [
    {
        "name": "retrieve_documents",
        "description": "Search document database for relevant information. Returns top chunks with similarity scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    }
]

def run_agent(user_question: str, max_iterations: int = 8) -> dict:
    """Run research agent with Think → Act → Observe loop."""
    messages = [
        {"role": "user", "content": f"Research and answer: {user_question}"}
    ]
    
    thoughts = []
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # THINK
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=messages,
            tools=tools,
        )
        
        thoughts.append({
            "iteration": iteration,
            "phase": "THINK",
            "content": response.text[:500],
        })
        
        # Check if done
        if not response.tool_calls:
            return {
                "status": "complete",
                "answer": response.text,
                "iterations": iteration,
                "thoughts": thoughts,
            }
        
        # ACT & OBSERVE
        for tool_call in response.tool_calls:
            if tool_call.name == "retrieve_documents":
                result = retrieve_documents(tool_call.args["query"])
                
                messages.append({"role": "assistant", "content": response.text})
                messages.append({
                    "role": "user",
                    "content": f"Tool result: {json.dumps(result, indent=2)}"
                })
                
                thoughts.append({
                    "iteration": iteration,
                    "phase": "ACT/OBSERVE",
                    "tool": "retrieve_documents",
                    "query": tool_call.args["query"],
                    "chunks_found": len(result.get("results", [])),
                })
    
    return {
        "status": "max_iterations_reached",
        "iterations": iteration,
        "thoughts": thoughts,
    }
```

### 2. FastAPI Endpoint (add to `main.py`)

```python
from agent_research import run_agent

@app.post("/agent")
def agent_endpoint(body: dict) -> dict:
    """Run research agent."""
    question = body.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question'")
    
    result = run_agent(question, max_iterations=8)
    return result
```

### 3. Streamlit UI (`streamlit_agent.py`)

```python
import streamlit as st
import httpx
import os

st.set_page_config(page_title="Week 3 Agent", page_icon="🤖")
st.title("🤖 Week 3: Research Agent")

API_URL = os.getenv("RAG_API_URL", "https://ai-engineering-wlqp.onrender.com")
st.markdown(f"**Live API:** `{API_URL}`")

question = st.text_area(
    "Ask a research question:",
    placeholder="What embedding models are discussed?",
    height=100,
)

if st.button("Run Agent", type="primary"):
    if not question:
        st.error("Please enter a question")
    else:
        with st.spinner("Agent thinking..."):
            try:
                response = httpx.post(
                    f"{API_URL}/agent",
                    json={"question": question},
                    timeout=30.0,
                )
                result = response.json()
                
                st.success(f"✓ Completed in {result.get('iterations', '?')} iterations")
                
                if "answer" in result:
                    st.subheader("Answer")
                    st.write(result["answer"])
                
                if "thoughts" in result:
                    with st.expander("Agent Thinking (Think → Act → Observe):"):
                        for thought in result["thoughts"]:
                            st.write(f"**Iteration {thought['iteration']} - {thought['phase']}**")
                            if "content" in thought:
                                st.write(thought["content"][:200])
                            if "chunks_found" in thought:
                                st.write(f"Found {thought['chunks_found']} relevant chunks")
                                
            except Exception as e:
                st.error(f"Error: {str(e)}")
```

## Environment Variables
```
GOOGLE_API_KEY=<your-google-api-key>
RAG_API_URL=https://ai-engineering-wlqp.onrender.com
```

## Test Command
```bash
curl -X POST https://ai-engineering-wlqp.onrender.com/agent \
  -H "Content-Type: application/json" \
  -d '{"question": "What embedding models are discussed in our documents?"}'
```

## Expected Flow

```
User: "What embedding models are discussed?"

Agent Iteration 1 [THINK]:
→ Model decides to search for embedding models

Agent Iteration 1 [ACT]:
→ Calls retrieve_documents("embedding models")

Agent Iteration 1 [OBSERVE]:
→ Receives 5 chunks about embeddings
→ Model analyzes and finds OpenAI models mentioned

Agent Iteration 2 [THINK]:
→ Enough info found, prepare answer

Result: Returns comprehensive answer with thinking steps
```

---

# 🔄 How Weeks Connect

```
Week 1: Simple API
    ↓
    + Retrieval (Week 2)
    ↓
Week 2: RAG (Linear, context-grounded)
    ↓
    + Looping logic (Week 3)
    ↓
Week 3: Agent (Multi-step, adaptive)
```

## Reused Components

| Component | Week 1 | Week 2 | Week 3 |
|-----------|--------|--------|--------|
| `/ask` endpoint | ✓ | ✓ (enhanced) | - |
| OpenAI API | ✓ | ✓ | ✓ (via Agent) |
| `/ingest` endpoint | - | ✓ | - |
| `/debug/retrieve` | - | ✓ | ✓ (as agent tool) |
| Pinecone | - | ✓ | ✓ (via retrieval) |
| Streamlit UI | ✓ | ✓ | ✓ |

---

# 📚 Quick Reference Commands

## Setup
```bash
# Week 1 & 2 (if not already done)
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt

# Week 3
pip install google-genai
```

## Run Locally

**Week 1 & 2 API:**
```bash
uvicorn main:app --port 8000
```

**Week 2 Streamlit:**
```bash
streamlit run streamlit_rag_app.py
```

**Week 3 Streamlit:**
```bash
streamlit run streamlit_agent.py
```

## Test Endpoints

**Week 1:**
```bash
curl -X POST http://localhost:8000/ask \
  -d '{"question": "What is RAG?", "use_rag": false}'
```

**Week 2:**
```bash
curl -X POST http://localhost:8000/ask \
  -d '{"question": "What is semantic search?", "use_rag": true}'
```

**Week 3:**
```bash
curl -X POST http://localhost:8000/agent \
  -d '{"question": "What embedding models are discussed?"}'
```

---

# 📋 File Structure

```
week-1/
├── main.py                       # FastAPI backend (Weeks 1, 2, 3)
├── agent_research.py             # Week 3 agent implementation
├── batch_ingest.py              # Week 2 document ingestion
├── streamlit_rag_app.py          # Week 2 RAG UI
├── streamlit_agent.py            # Week 3 Agent UI
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── WEEK1_SUMMARY.md             # Week 1 details
├── WEEK2_EVIDENCE.md            # Week 2 proof & evidence
├── WEEK3_SETUP.md               # Week 3 setup guide
└── COMPLETE_BOOTCAMP_REFERENCE.md  # This file
```

---

# ✅ Completion Checklist

**Week 1:**
- ✅ `/ask` endpoint working
- ✅ Token tracking
- ✅ Cost calculation
- ✅ Deployed to Render
- ✅ Streamlit UI working

**Week 2:**
- ✅ `/ingest` endpoint working
- ✅ `/debug/retrieve` endpoint working
- ✅ `/ask` enhanced with RAG
- ✅ Pinecone integration
- ✅ Document corpus ingested
- ✅ Citations & refusals working
- ✅ Deployed to Render

**Week 3:**
- [ ] Agent setup complete
- [ ] Tool integration working
- [ ] Think → Act → Observe loop visible
- [ ] Streamlit UI functional
- [ ] Deployed to Render
- [ ] Agent vs. workflow justified

---

**Save this file for reference across all three weeks!**
