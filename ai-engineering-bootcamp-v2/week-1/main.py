"""Week 1 live demo — five stages in one file, built up live in class."""

import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pinecone import Pinecone
from pydantic import BaseModel, Field, ValidationError

# Load .env from this folder so the key is found regardless of shell working directory.
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)

# Reuse one client so TLS handshakes are not repeated on every request.
app = FastAPI()
client = OpenAI()  # Reads OPENAI_API_KEY from the environment; never hardcode keys.

# Week 2: Pinecone vector store for RAG
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ai-engineer-rag")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

# Initialize Pinecone if API key is available (optional for local testing)
pinecone_client = None
if PINECONE_API_KEY:
    try:
        pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Pinecone: {e}")

# Embedding model for RAG
EMBEDDING_MODEL = "text-embedding-3-small"


def ensure_pinecone_index():
    """Create Pinecone index if it doesn't exist."""
    if not pinecone_client:
        return False

    try:
        # Try to get the index
        index = pinecone_client.Index(PINECONE_INDEX_NAME)
        index.describe_index_stats()
        print(f"Pinecone index '{PINECONE_INDEX_NAME}' already exists")
        return True
    except Exception as e:
        if "not found" in str(e).lower():
            print(f"Creating Pinecone index '{PINECONE_INDEX_NAME}'...")
            try:
                pinecone_client.create_index(
                    name=PINECONE_INDEX_NAME,
                    dimension=1536,  # text-embedding-3-small dimension
                    metric="cosine",
                    spec={
                        "serverless": {
                            "cloud": "aws",
                            "region": "us-east-1"
                        }
                    }
                )
                print(f"Index '{PINECONE_INDEX_NAME}' created successfully")
                return True
            except Exception as create_error:
                print(f"Error creating index: {create_error}")
                return False
        else:
            print(f"Error checking index: {e}")
            return False


# Health check endpoint for Render deployment
@app.get("/health")
def health():
    """Health check including Pinecone connectivity."""
    health_status = {"status": "ok", "openai": "connected", "pinecone": "not_configured"}

    # Check Pinecone connectivity
    if pinecone_client:
        try:
            index = pinecone_client.Index(PINECONE_INDEX_NAME)
            stats = index.describe_index_stats()
            health_status["pinecone"] = "connected"
            health_status["pinecone_dimensions"] = stats.dimension
            health_status["pinecone_vectors"] = stats.total_vector_count
        except Exception as e:
            health_status["pinecone"] = f"error: {str(e)}"

    return health_status

# Stage 4 default — strong general model; swap at request time for the live demo.
DEFAULT_MODEL = "gpt-4o"

# Stage 5 — per-1K-token input/output USD (derived from OpenAI list prices).
MODEL_PRICES_PER_1K: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "o3-mini": (0.0011, 0.0044),
}


class Answer(BaseModel):
    """Structured model output — this is what turns a chatbot into a component."""

    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources_needed: bool


class AskRequest(BaseModel):
    """Typed request body so bad input is rejected before we spend tokens."""

    question: str
    force_bad: bool = False  # Stage 3 demo knob — first attempt breaks schema on purpose.
    model: str | None = None  # Stage 4 — optional override to swap models live.
    use_rag: bool = True  # Week 2 — enable/disable RAG retrieval


class AskResponse(BaseModel):
    """Typed response so callers always get the same shape back."""

    answer: Answer
    tokens_used: int
    model: str
    latency_ms: int
    cost_usd: float
    citations: list[str] | None = None  # Week 2 — document_ids used in answer
    retrieved_chunks: int | None = None  # Week 2 — how many chunks were retrieved


# Week 2: RAG Models
class IngestRequest(BaseModel):
    """Request to ingest a document into the vector store."""

    text: str
    document_id: str
    metadata: dict | None = None  # Optional source filename, etc.


class IngestResponse(BaseModel):
    """Response from document ingestion."""

    document_id: str
    chunks_indexed: int
    status: str


class RetrieveResult(BaseModel):
    """Single chunk retrieved from vector store."""

    chunk_id: str
    text: str
    similarity_score: float
    metadata: dict


def compute_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Turn real usage into dollars — same prompt, different model, different cost."""

    prices = MODEL_PRICES_PER_1K.get(model, MODEL_PRICES_PER_1K[DEFAULT_MODEL])
    input_per_1k, output_per_1k = prices
    return (prompt_tokens / 1000 * input_per_1k) + (completion_tokens / 1000 * output_per_1k)


def call_model_structured(question: str, model: str, context: str | None = None) -> tuple[Answer, int, int, int]:
    """
    Stage 2 center: OpenAI structured output forces exactly the Answer schema.
    Returns parsed answer plus token counts from billing metadata.

    If context is provided (Week 2 RAG), grounds the response in that context.
    """

    # Build the message content
    if context:
        # RAG grounding prompt
        content = (
            f"Answer using ONLY the context below. "
            f"If the context does not contain enough information to answer, respond with: "
            f"'I don't have enough information to answer that question based on the available documents.'\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}"
        )
    else:
        # Regular prompt (no context)
        content = question

    completion = client.chat.completions.parse(
        model=model,
        messages=[{"role": "user", "content": content}],
        response_format=Answer,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Model returned no parseable structured output")

    usage = completion.usage
    total = usage.total_tokens if usage else 0
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    return parsed, total, prompt_tokens, completion_tokens


def call_model_unsafe(question: str, model: str) -> tuple[Answer, int, int, int]:
    """
    Stage 3 demo path: free-form JSON call, then validate locally.
    The bad instruction makes confidence a string so Pydantic rejects it reliably.
    """

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": (
                    f"{question}\n\n"
                    "Reply with ONLY a JSON object using keys answer, confidence, sources_needed. "
                    "Set confidence to the string 'very high' (not a number)."
                ),
            }
        ],
    )

    raw = completion.choices[0].message.content or ""
    # Guardrail: refuse malformed output instead of passing it through to clients.
    answer = Answer.model_validate_json(raw)

    usage = completion.usage
    total = usage.total_tokens if usage else 0
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    return answer, total, prompt_tokens, completion_tokens


# Week 2: RAG Helper Functions
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks using RecursiveCharacterTextSplitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    return splitter.split_text(text)


def embed_text(text: str) -> list[float]:
    """Generate embedding for text using text-embedding-3-small."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def upsert_to_pinecone(
    document_id: str, chunks: list[str], metadata: dict | None = None
) -> int:
    """Upsert chunks to Pinecone with metadata."""
    if not pinecone_client:
        raise ValueError("Pinecone client not initialized")

    index = pinecone_client.Index(PINECONE_INDEX_NAME)
    vectors_to_upsert = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"{document_id}#{i}"
        embedding = embed_text(chunk)

        chunk_metadata = {
            "document_id": document_id,
            "chunk_index": i,
            "text": chunk,
            **(metadata or {}),
        }

        vectors_to_upsert.append((chunk_id, embedding, chunk_metadata))

    # Upsert in batches
    batch_size = 100
    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i : i + batch_size]
        index.upsert(vectors=batch)

    return len(vectors_to_upsert)


def retrieve_context(question: str, top_k: int = 5) -> tuple[str, list[str]]:
    """
    Retrieve top-k chunks from Pinecone and format as context for LLM.
    Returns (formatted_context, document_ids_cited).
    """
    if not pinecone_client:
        return "", []

    try:
        # Embed the question
        query_embedding = embed_text(question)

        # Retrieve from Pinecone
        index = pinecone_client.Index(PINECONE_INDEX_NAME)
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )

        # Format context
        context_pieces = []
        cited_docs = set()

        for match in results.matches:
            metadata = match.metadata or {}
            text = metadata.get("text", "")
            doc_id = metadata.get("document_id", "unknown")

            if text:
                context_pieces.append(f"[{doc_id}] {text}")
                cited_docs.add(doc_id)

        context = "\n\n".join(context_pieces) if context_pieces else ""
        return context, list(cited_docs)

    except Exception as e:
        print(f"Error retrieving context: {e}")
        return "", []


@app.post("/ask")
def ask(body: AskRequest) -> AskResponse:
    """Answer one question with structured output, guardrails, and cost visibility.

    Week 2 enhancement: Supports RAG with context retrieval and citations.
    """

    model = body.model or DEFAULT_MODEL
    last_error: str | None = None

    # Week 2: Retrieve context if RAG is enabled
    context = ""
    citations = None
    retrieved_chunks = 0

    if body.use_rag and pinecone_client:
        context, citations = retrieve_context(body.question, top_k=5)
        retrieved_chunks = len(citations)

    # Stage 3: one retry keeps the logic legible while still protecting callers.
    for attempt in range(2):
        try:
            start = time.perf_counter()

            # First attempt with force_bad uses the unsafe path; retry uses structured output.
            use_bad_path = body.force_bad and attempt == 0
            if use_bad_path:
                answer, tokens_used, prompt_tokens, completion_tokens = call_model_unsafe(
                    body.question, model
                )
            else:
                # Week 2: Pass context to structured call if RAG is enabled
                answer, tokens_used, prompt_tokens, completion_tokens = call_model_structured(
                    body.question, model, context=context if body.use_rag else None
                )

            latency_ms = int((time.perf_counter() - start) * 1000)
            cost_usd = compute_cost_usd(model, prompt_tokens, completion_tokens)

            return AskResponse(
                answer=answer,
                tokens_used=tokens_used,
                model=model,
                latency_ms=latency_ms,
                cost_usd=round(cost_usd, 6),
                citations=citations,
                retrieved_chunks=retrieved_chunks,
            )
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            continue

    # Clean failure — never leak a half-parsed response to the client.
    raise HTTPException(
        status_code=502,
        detail=f"Model response failed schema validation after retry: {last_error}",
    )


@app.get("/debug/retrieve")
def debug_retrieve(q: str) -> list[RetrieveResult]:
    """
    Debug endpoint: embed query and retrieve top-5 chunks from vector store.
    Does NOT invoke LLM — purely for testing retrieval quality.
    """

    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' cannot be empty")

    if not pinecone_client:
        raise HTTPException(status_code=503, detail="Vector store not configured")

    try:
        # Embed the query
        query_embedding = embed_text(q)

        # Retrieve top-5 from Pinecone
        index = pinecone_client.Index(PINECONE_INDEX_NAME)
        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
        )

        # Format results
        retrieved = []
        for match in results.matches:
            metadata = match.metadata or {}
            retrieved.append(
                RetrieveResult(
                    chunk_id=match.id,
                    text=metadata.get("text", ""),
                    similarity_score=match.score,
                    metadata={k: v for k, v in metadata.items() if k != "text"},
                )
            )

        return retrieved

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@app.post("/ingest")
def ingest(body: IngestRequest) -> IngestResponse:
    """Ingest a document into the vector store for RAG."""

    # Validate input
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text field cannot be empty")

    if not body.document_id or not body.document_id.strip():
        raise HTTPException(status_code=400, detail="document_id field cannot be empty")

    if not pinecone_client:
        raise HTTPException(
            status_code=503, detail="Vector store not configured"
        )

    try:
        # Chunk the text
        chunks = chunk_text(body.text)

        if not chunks:
            raise HTTPException(status_code=400, detail="Text could not be chunked")

        # Upsert to Pinecone
        chunks_indexed = upsert_to_pinecone(
            document_id=body.document_id,
            chunks=chunks,
            metadata=body.metadata or {},
        )

        return IngestResponse(
            document_id=body.document_id,
            chunks_indexed=chunks_indexed,
            status="success",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ingestion failed: {str(e)}"
        )
