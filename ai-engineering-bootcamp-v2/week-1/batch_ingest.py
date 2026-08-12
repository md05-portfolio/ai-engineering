"""
Week 2 RAG: Batch ingest documents into vector store.
Loads sample documents and reports statistics.
"""

import httpx
import json
from pathlib import Path

# Base URL for the API (can be localhost for testing or live Render URL)
API_BASE_URL = "http://127.0.0.1:8000"

# Sample documents for batch ingestion
DOCUMENTS = [
    {
        "document_id": "rag-fundamentals-001",
        "source": "AI Fundamentals",
        "text": """Retrieval-Augmented Generation (RAG) is a technique that combines retrieval of relevant
documents with a generative model to produce more accurate and contextually informed responses.
RAG systems first retrieve relevant documents from a knowledge base, then use these retrieved
documents as context for the language model to generate answers. This approach significantly
improves the quality and accuracy of generated text by grounding the model in factual information.
RAG is particularly useful for applications requiring up-to-date information, domain-specific
knowledge, or reduced hallucinations. The retrieval component can use various similarity metrics
such as BM25, semantic similarity, or dense vector embeddings. The generative component then
conditions its output on the retrieved documents to ensure factuality.""",
    },
    {
        "document_id": "embeddings-guide-002",
        "source": "Embeddings Technical Guide",
        "text": """Embeddings are dense vector representations of text, images, or other data types that
capture semantic meaning. Modern embeddings are typically generated using transformer-based models
like BERT, GPT, or specialized embedding models. Embeddings allow computers to understand similarity
between pieces of text based on meaning rather than exact word matching. For example, 'car' and
'automobile' will have very similar embedding vectors despite different wording. Common embedding
models include OpenAI's text-embedding-3-small and text-embedding-3-large, which produce
1536-dimensional and 3072-dimensional vectors respectively. Embeddings are fundamental to RAG systems
as they enable semantic search and retrieval based on meaning rather than keywords.""",
    },
    {
        "document_id": "vector-db-overview-003",
        "source": "Vector Database Systems",
        "text": """Vector databases are specialized systems designed to store and efficiently search
high-dimensional vectors. Unlike traditional databases optimized for tabular data, vector databases
use algorithms like Hierarchical Navigable Small World (HNSW), Product Quantization, and Locality
Sensitive Hashing for fast approximate nearest neighbor search. Popular vector databases include
Pinecone, Weaviate, Milvus, and Qdrant. Pinecone is a fully managed cloud service that simplifies
vector storage and retrieval. Weaviate is open-source and self-hosted. Milvus supports multiple
deployment options. These databases can handle billions of vectors and provide sub-millisecond
query latency. Vector databases are critical infrastructure for modern AI applications including
semantic search, recommendation systems, and retrieval-augmented generation.""",
    },
    {
        "document_id": "llm-prompting-004",
        "source": "LLM Prompting Best Practices",
        "text": """Large Language Models (LLMs) can be guided to produce better outputs through careful
prompt engineering. Key techniques include: 1) Providing clear instructions about the task, 2) Giving
examples of desired behavior (few-shot learning), 3) Breaking complex tasks into steps, 4) Specifying
output format explicitly, 5) Using role-based prompting ('Act as an expert in...'), 6) Temperature
and sampling controls to tune creativity vs consistency. When using RAG, grounding prompts are
especially important - instructing the model to only use provided context and refuse to answer when
context is insufficient. This prevents hallucinations and keeps responses factual. Structured output
formats like JSON schemas can enforce specific response structures when using newer models with
structured output capabilities.""",
    },
    {
        "document_id": "semantic-search-005",
        "source": "Semantic Search Implementation",
        "text": """Semantic search finds relevant documents based on meaning rather than keyword matching.
The process involves: 1) Converting queries and documents to embeddings, 2) Computing similarity
between query and document embeddings using metrics like cosine similarity or Euclidean distance,
3) Ranking and returning top-k most similar results. Semantic search excels at understanding intent
and synonyms. For example, searching for 'fast cars' retrieves documents about 'rapid automobiles'
even without exact keyword overlap. Semantic search is the foundation of RAG systems, enabling
retrieval of contextually relevant information. Hybrid search approaches combine semantic search with
keyword search to leverage strengths of both methods. Re-ranking techniques can further improve
relevance by using more sophisticated models to score top candidates.""",
    },
]


def ingest_document(doc_id: str, text: str, source: str) -> dict:
    """Ingest a single document via the /ingest endpoint."""
    payload = {
        "document_id": doc_id,
        "text": text,
        "metadata": {"source": source},
    }

    try:
        response = httpx.post(
            f"{API_BASE_URL}/ingest",
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "document_id": doc_id}


def batch_ingest_documents():
    """Ingest all sample documents and report statistics."""
    print(f"Starting batch ingestion to {API_BASE_URL}")
    print(f"Total documents to ingest: {len(DOCUMENTS)}\n")

    results = []
    total_chunks = 0

    for doc in DOCUMENTS:
        print(f"Ingesting {doc['document_id']} from {doc['source']}...", end=" ")
        result = ingest_document(doc["document_id"], doc["text"], doc["source"])

        if "error" in result:
            print(f"[FAILED] {result['error']}")
        else:
            chunks = result.get("chunks_indexed", 0)
            total_chunks += chunks
            status = result.get("status", "unknown")
            print(f"[OK] {chunks} chunks, status: {status}")
            results.append(result)

    print(f"\n{'='*60}")
    print(f"Batch Ingestion Summary")
    print(f"{'='*60}")
    print(f"Documents ingested: {len(results)}/{len(DOCUMENTS)}")
    print(f"Total chunks indexed: {total_chunks}")
    print(f"Average chunks per document: {total_chunks / len(results) if results else 0:.1f}")

    # Get health stats to show vector store size
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=10.0)
        health = response.json()
        pinecone_vectors = health.get("pinecone_vectors", 0)
        pinecone_dims = health.get("pinecone_dimensions", 0)
        print(f"\nPinecone Vector Store:")
        print(f"  Total vectors: {pinecone_vectors}")
        print(f"  Dimensions: {pinecone_dims}")
    except Exception as e:
        print(f"Could not fetch health stats: {e}")

    print(f"\n[COMPLETE] Batch ingestion complete!")
    return results


if __name__ == "__main__":
    batch_ingest_documents()
