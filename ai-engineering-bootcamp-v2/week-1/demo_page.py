"""
Week 2 RAG Application - Streamlit UI
Interactive interface for document ingestion and RAG queries.
Points to live Render API by default.
"""

import os
import streamlit as st
import httpx
import json

# Configuration
API_BASE_URL = os.getenv("RAG_API_URL", "https://ai-engineering-wlqp.onrender.com")
DEFAULT_MODEL = "gpt-4o-mini"

# Page configuration
st.set_page_config(
    page_title="Week 2 RAG Demo",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Week 2: Retrieval-Augmented Generation Demo")
st.markdown(
    f"**Live API:** `{API_BASE_URL}`  |  **Status:** Check health endpoint"
)

# Sidebar configuration
st.sidebar.header("Configuration")
mode = st.sidebar.radio("Select Mode:", ["Query RAG", "Ingest Document"], index=0)
use_rag = st.sidebar.checkbox("Enable RAG (uncheck for regular LLM)", value=True)
model = st.sidebar.selectbox(
    "Model",
    ["gpt-4o-mini", "gpt-4o", "o3-mini"],
    index=0,
)

# Initialize session state
if "ingest_results" not in st.session_state:
    st.session_state.ingest_results = []
if "query_results" not in st.session_state:
    st.session_state.query_results = None


def fetch_health():
    """Get health status from API."""
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=10.0)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def ingest_document(text: str, doc_id: str, metadata: dict = None):
    """Call ingest endpoint."""
    try:
        payload = {"text": text, "document_id": doc_id, "metadata": metadata or {}}
        response = httpx.post(
            f"{API_BASE_URL}/ingest",
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def query_rag(question: str, use_rag: bool = True):
    """Call ask endpoint with RAG."""
    try:
        payload = {"question": question, "model": model, "use_rag": use_rag}
        response = httpx.post(
            f"{API_BASE_URL}/ask",
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def retrieve_debug(query: str):
    """Call debug/retrieve endpoint."""
    try:
        response = httpx.get(
            f"{API_BASE_URL}/debug/retrieve",
            params={"q": query},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# Mode: Query RAG
if mode == "Query RAG":
    st.header("Query RAG System")

    col1, col2 = st.columns([3, 1])
    with col1:
        question = st.text_area(
            "Ask a question:",
            placeholder="What is semantic search?",
            height=100,
        )
    with col2:
        st.markdown("")
        st.markdown("")
        query_button = st.button("Submit Query", type="primary", use_container_width=True)

    if query_button and question:
        with st.spinner("Querying RAG system..."):
            result = query_rag(question, use_rag=use_rag)

        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            st.session_state.query_results = result

    # Display results
    if st.session_state.query_results:
        result = st.session_state.query_results

        # Answer section
        st.subheader("Answer")
        answer_obj = result.get("answer", {})
        answer_text = answer_obj.get("answer", "No answer provided")
        confidence = answer_obj.get("confidence", 0)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Confidence", f"{confidence:.0%}")
        with col2:
            st.metric("Tokens Used", result.get("tokens_used", 0))
        with col3:
            st.metric("Cost (USD)", f"${result.get('cost_usd', 0):.6f}")

        st.markdown(answer_text)

        # Citations section
        citations = result.get("citations")
        if citations:
            st.subheader("Citations")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Retrieved from {len(citations)} document(s):**")
            with col2:
                st.caption(f"Chunks retrieved: {result.get('retrieved_chunks', 0)}")

            for doc_id in citations:
                st.write(f"📄 `{doc_id}`")

        # Metadata
        with st.expander("Metadata"):
            st.json(
                {
                    "model": result.get("model"),
                    "latency_ms": result.get("latency_ms"),
                    "rag_enabled": use_rag,
                }
            )

        # Debug retrieval
        if st.checkbox("Show Retrieved Chunks"):
            with st.spinner("Fetching retrieved chunks..."):
                chunks = retrieve_debug(question)

            if "error" not in chunks:
                for i, chunk in enumerate(chunks[:5], 1):
                    with st.expander(
                        f"Chunk {i}: {chunk['chunk_id']} (score: {chunk['similarity_score']:.3f})"
                    ):
                        st.write(chunk["text"])
                        st.caption(f"Metadata: {chunk['metadata']}")

# Mode: Ingest Document
elif mode == "Ingest Document":
    st.header("Ingest Document into Vector Store")

    col1, col2 = st.columns([2, 1])

    with col1:
        doc_text = st.text_area(
            "Document text:",
            placeholder="Paste your document here...",
            height=150,
        )

    with col2:
        doc_id = st.text_input(
            "Document ID:",
            placeholder="e.g., doc-001",
        )
        source = st.text_input(
            "Source (optional):",
            placeholder="e.g., tutorial.md",
        )
        ingest_button = st.button("Ingest", type="primary", use_container_width=True)

    if ingest_button:
        if not doc_text or not doc_id:
            st.error("Please provide both document text and ID")
        else:
            with st.spinner("Ingesting document..."):
                metadata = {"source": source} if source else {}
                result = ingest_document(doc_text, doc_id, metadata)

            if "error" in result:
                st.error(f"Ingestion failed: {result['error']}")
            else:
                st.success(f"Ingestion successful!")
                chunks_indexed = result.get("chunks_indexed", 0)
                st.metric("Chunks Indexed", chunks_indexed)
                st.session_state.ingest_results.append(result)

    # History
    if st.session_state.ingest_results:
        st.subheader("Ingestion History")
        for i, res in enumerate(st.session_state.ingest_results):
            st.write(
                f"{i+1}. **{res['document_id']}** - {res['chunks_indexed']} chunks ({res['status']})"
            )

# Sidebar: Health check
st.sidebar.divider()
st.sidebar.subheader("System Status")
if st.sidebar.button("Check Health", use_container_width=True):
    with st.spinner("Checking health..."):
        health = fetch_health()

    if "error" in health:
        st.sidebar.error(f"API Error: {health['error']}")
    else:
        st.sidebar.success("System healthy!")
        st.sidebar.metric("OpenAI", health.get("openai", "unknown"))
        st.sidebar.metric("Pinecone", health.get("pinecone", "unknown"))
        st.sidebar.metric("Vectors Indexed", health.get("pinecone_vectors", 0))
        st.sidebar.caption(f"Dims: {health.get('pinecone_dimensions', 0)}")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔗 [Live API](https://ai-engineering-wlqp.onrender.com)")
with col2:
    st.caption("📚 [GitHub](https://github.com/md05-portfolio/ai-engineering)")
with col3:
    st.caption("📖 [Week 2 Docs](https://github.com/md05-portfolio/ai-engineering/blob/main/ai-engineering-bootcamp-v2/week-1/WEEK2_DEMONSTRATION.md)")
