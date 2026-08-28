"""
Week 4: Sample Traces Generator
Creates realistic sample traces for evaluation testing and annotation.
This simulates agent runs with various success/failure patterns.
"""

from week4_trace_capture import Trace, TraceStore, FailureCategory
from datetime import datetime, timedelta
import random
import uuid


def generate_sample_traces(count: int = 20) -> list[Trace]:
    """Generate realistic sample traces with various success/failure patterns."""

    sample_questions = [
        "What embedding models are discussed in our documents?",
        "How does vector search work?",
        "What are best practices for RAG?",
        "Explain the concept of semantic search.",
        "What is Pinecone?",
        "How do I implement retrieval augmented generation?",
        "What are the benefits of vector databases?",
        "Describe attention mechanisms in transformers.",
        "What is a language model?",
        "How does fine-tuning work?",
        "What are the latest advances in AI?",
        "Explain zero-shot learning.",
        "What is transfer learning?",
        "How do embeddings work?",
        "What are hallucinations in LLMs?",
        "How to evaluate language models?",
        "What is prompt engineering?",
        "Explain few-shot prompting.",
        "What are multi-modal models?",
        "How do agents differ from chatbots?",
    ]

    success_answers = [
        "Embedding models like text-embedding-3-small convert text to high-dimensional vectors. These are used in our RAG system for semantic search.",
        "Vector search works by converting queries to embeddings and finding similar vectors in a vector database like Pinecone.",
        "Best practices for RAG include: (1) good chunking strategy, (2) semantic relevance of retrieval, (3) prompt engineering for grounding.",
        "Semantic search uses embeddings to find conceptually similar documents rather than keyword matching.",
        "Pinecone is a managed vector database that scales semantic search. It's optimized for low-latency retrieval.",
        "RAG combines retrieval and generation: retrieve relevant documents, then pass as context to the LLM.",
        "Vector databases enable fast approximate nearest neighbor search, crucial for real-time AI applications.",
        "Attention mechanisms allow transformers to weight different parts of input differently, improving context understanding.",
        "Language models are neural networks trained on text to predict next tokens, enabling various NLP tasks.",
        "Fine-tuning adapts a pre-trained model to specific tasks by training on task-specific data.",
    ]

    failure_answers = [
        "I don't have enough information to answer that based on the available documents.",
        "This question is about a topic I'm not familiar with.",
        "I cannot provide a complete answer to that question.",
        "The documents don't contain information about that topic.",
        "This topic hasn't been covered in our knowledge base.",
    ]

    incomplete_answers = [
        "Embeddings are representations of text.",
        "RAG is a technique.",
        "Vector databases are databases.",
    ]

    traces = []
    base_time = datetime.now() - timedelta(hours=100)

    for i in range(count):
        trace_id = str(uuid.uuid4())[:8]
        timestamp = (base_time + timedelta(minutes=i * 5)).isoformat()
        question = random.choice(sample_questions)

        # Vary the outcomes: 60% success, 30% incomplete/failures, 10% errors
        outcome_type = random.random()

        if outcome_type < 0.60:
            # Successful execution
            answer = random.choice(success_answers)
            status = "complete"
            success = True
            iterations = random.randint(1, 3)
            retrieved_chunks = random.randint(3, 5)
            failure_category = None
            annotator_notes = "Good answer with relevant retrieval"

        elif outcome_type < 0.80:
            # Incomplete or hallucinated answer
            if random.random() < 0.5:
                answer = random.choice(incomplete_answers)
                failure_category = FailureCategory.INCOMPLETE_ANSWER
                annotator_notes = "Answer is too brief and doesn't fully address the question"
            else:
                answer = "Based on our advanced AI research, quantum embeddings are the future of semantic search."
                failure_category = FailureCategory.HALLUCINATION
                annotator_notes = "Answer contains false information not in documents"

            status = "complete"
            success = False
            iterations = random.randint(1, 3)
            retrieved_chunks = random.randint(2, 4)

        else:
            # Error or retrieval failure
            if random.random() < 0.5:
                answer = None
                failure_category = FailureCategory.RETRIEVAL_FAILURE
                annotator_notes = "No relevant documents retrieved"
                status = "error"
                retrieved_chunks = 0
            else:
                answer = "Processing error occurred during retrieval."
                failure_category = FailureCategory.API_ERROR
                annotator_notes = "API call failed"
                status = "error"
                retrieved_chunks = 0

            success = False
            iterations = random.randint(1, 2)

        latency_ms = random.randint(500, 5000) if success else random.randint(2000, 8000)

        trace = Trace(
            trace_id=trace_id,
            timestamp=timestamp,
            question=question,
            answer=answer,
            status=status,
            iterations=iterations,
            latency_ms=latency_ms,
            model="gemini-3.5-flash",
            failure_category=failure_category,
            annotator_notes=annotator_notes,
            success=success,
            retrieval_queries=[question] if retrieved_chunks > 0 else [],
            retrieved_chunks_count=retrieved_chunks,
            citations=[f"doc_{j}" for j in range(retrieved_chunks)],
        )

        traces.append(trace)

    return traces


def save_sample_traces_to_store(traces: list[Trace], store_path: str = "./traces"):
    """Save sample traces to TraceStore."""
    store = TraceStore(traces_dir=store_path)

    # Clear existing traces to avoid duplicates
    import shutil
    from pathlib import Path
    traces_path = Path(store_path)
    if traces_path.exists():
        shutil.rmtree(traces_path)
    traces_path.mkdir(exist_ok=True)

    for trace in traces:
        store.save_trace(trace)
        print(f"Saved trace {trace.trace_id}: {trace.status}")

    return store


if __name__ == "__main__":
    print("Generating 20 sample traces for Week 4 evaluation...")
    samples = generate_sample_traces(count=20)
    print(f"Generated {len(samples)} traces")

    print("\nSaving to ./traces directory...")
    store = save_sample_traces_to_store(samples)

    print("\nTrace Summary:")
    summary = store.get_failure_summary()
    print(f"Total traces: {summary['total_traces']}")
    print(f"Annotated: {summary['annotated']}")
    print(f"Successful: {summary['success_count']}")
    print(f"Failed: {summary['failure_count']}")
    print(f"\nFailures by category:")
    for category, count in summary["by_category"].items():
        print(f"  - {category}: {count}")
