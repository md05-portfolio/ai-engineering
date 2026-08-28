"""
Week 4: Trace Capture System
Captures detailed traces from agent runs for evaluation and analysis.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Any
from enum import Enum


class FailureCategory(Enum):
    """Failure taxonomy for the evaluation system."""

    # Real failures observed in the system
    HALLUCINATION = "hallucination"  # Model generates false information
    INCOMPLETE_ANSWER = "incomplete_answer"  # Doesn't fully answer the question
    RETRIEVAL_FAILURE = "retrieval_failure"  # Failed to retrieve relevant documents
    SCHEMA_VIOLATION = "schema_violation"  # Output doesn't match expected schema
    NO_SEARCH_TRIGGER = "no_search_trigger"  # Didn't search when should have
    IRRELEVANT_SEARCH = "irrelevant_search"  # Searched but got irrelevant results
    TIMEOUT = "timeout"  # Call took too long or timed out
    API_ERROR = "api_error"  # Underlying API/service error


@dataclass
class Trace:
    """Single trace from agent execution."""

    trace_id: str
    timestamp: str
    question: str
    answer: Optional[str]
    status: str  # "success", "error", "incomplete", "timeout"
    iterations: int
    latency_ms: int
    model: str

    # Evaluation fields
    failure_category: Optional[FailureCategory] = None
    annotator_notes: str = ""
    success: bool = True

    # Detailed execution data
    retrieval_queries: list[str] = None
    retrieved_chunks_count: int = 0
    citations: list[str] = None
    thoughts: list[dict] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.retrieval_queries is None:
            self.retrieval_queries = []
        if self.citations is None:
            self.citations = []
        if self.thoughts is None:
            self.thoughts = []

    def to_dict(self) -> dict:
        """Convert to dictionary, handling enums."""
        data = asdict(self)
        if self.failure_category:
            data['failure_category'] = self.failure_category.value
        return data

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class TraceStore:
    """Persistent trace storage with file-based backend."""

    def __init__(self, traces_dir: str = "./traces"):
        self.traces_dir = Path(traces_dir)
        self.traces_dir.mkdir(exist_ok=True)
        self.traces = []
        self._load_traces()

    def _load_traces(self):
        """Load all existing traces from disk."""
        self.traces = []
        for trace_file in self.traces_dir.glob("trace_*.json"):
            try:
                with open(trace_file) as f:
                    data = json.load(f)
                    # Reconstruct Trace object
                    if 'failure_category' in data and data['failure_category']:
                        data['failure_category'] = FailureCategory(data['failure_category'])
                    trace = Trace(**data)
                    self.traces.append(trace)
            except Exception as e:
                print(f"Error loading trace {trace_file}: {e}")

    def save_trace(self, trace: Trace) -> str:
        """Save trace to disk and add to in-memory store."""
        filename = self.traces_dir / f"trace_{trace.trace_id}.json"
        with open(filename, 'w') as f:
            f.write(trace.to_json())
        self.traces.append(trace)
        return str(filename)

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a single trace by ID."""
        for trace in self.traces:
            if trace.trace_id == trace_id:
                return trace
        return None

    def get_all_traces(self) -> list[Trace]:
        """Get all traces."""
        return self.traces

    def update_trace_annotation(
        self,
        trace_id: str,
        failure_category: Optional[FailureCategory],
        annotator_notes: str
    ) -> bool:
        """Update trace with annotation data."""
        trace = self.get_trace(trace_id)
        if not trace:
            return False

        trace.failure_category = failure_category
        trace.annotator_notes = annotator_notes
        trace.success = failure_category is None

        # Save updated trace
        filename = self.traces_dir / f"trace_{trace_id}.json"
        with open(filename, 'w') as f:
            f.write(trace.to_json())

        return True

    def get_failure_summary(self) -> dict:
        """Get summary of failures by category."""
        summary = {
            "total_traces": len(self.traces),
            "annotated": 0,
            "success_count": 0,
            "failure_count": 0,
            "by_category": {}
        }

        for trace in self.traces:
            if trace.annotator_notes:
                summary["annotated"] += 1

            if trace.success:
                summary["success_count"] += 1
            else:
                summary["failure_count"] += 1
                if trace.failure_category:
                    cat = trace.failure_category.value
                    summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1

        return summary

    def get_failures_by_category(self, category: FailureCategory) -> list[Trace]:
        """Get all traces with a specific failure category."""
        return [t for t in self.traces if t.failure_category == category]


def create_trace_from_agent_response(
    response: dict,
    question: str,
    latency_ms: int,
    model: str = "gemini-3.5-flash"
) -> Trace:
    """Create a Trace object from agent API response."""
    import uuid

    trace_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().isoformat()

    status = response.get('status', 'unknown')
    answer = response.get('answer', None)
    error_msg = response.get('error', None)
    iterations = response.get('iterations', 0)
    thoughts = response.get('thoughts', [])

    # Determine success
    success = status == "complete"

    # Extract retrieval information from thoughts
    retrieval_queries = []
    retrieved_chunks = 0
    for thought in thoughts:
        if thought.get('phase') == 'ACT/OBSERVE':
            if thought.get('query'):
                retrieval_queries.append(thought['query'])
            if thought.get('found'):
                retrieved_chunks = max(retrieved_chunks, thought['found'])

    trace = Trace(
        trace_id=trace_id,
        timestamp=timestamp,
        question=question,
        answer=answer,
        status=status,
        iterations=iterations,
        latency_ms=latency_ms,
        model=model,
        retrieval_queries=retrieval_queries,
        retrieved_chunks_count=retrieved_chunks,
        thoughts=thoughts,
        error_message=error_msg,
        success=success
    )

    return trace
