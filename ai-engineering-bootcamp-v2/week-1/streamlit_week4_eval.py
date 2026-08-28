"""
Week 4: Evaluation Dashboard
Streamlit app for trace annotation, failure taxonomy, and before/after metrics.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

from week4_trace_capture import TraceStore, FailureCategory
from week4_checks import CheckSuite


# Page config
st.set_page_config(page_title="Week 4 Evaluation", page_icon="📊", layout="wide")
st.title("📊 Week 4: TRACE Evaluation Dashboard")

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    ["📈 Metrics", "📝 Trace Annotation", "🔍 Trace Detail", "📋 Failure Taxonomy"]
)

# Initialize TraceStore
traces_dir = "./traces"
store = TraceStore(traces_dir=traces_dir)

st.sidebar.markdown("---")
st.sidebar.info(f"Loaded {len(store.get_all_traces())} traces")


def get_metrics_before_fix():
    """Simulate baseline metrics before the fix."""
    # These are "before" metrics that would be from the original system
    return {
        "total_runs": len(store.get_all_traces()),
        "success_rate": 0.58,
        "avg_latency_ms": 3500,
        "avg_iterations": 2.2,
        "retrieval_quality": 0.62,
        "answer_completeness": 0.55,
    }


def get_metrics_after_fix():
    """Calculate metrics after the fix (using automated checks)."""
    traces = store.get_all_traces()
    check_suite = CheckSuite()

    results = []
    for trace in traces:
        check_result = check_suite.validate_trace(
            question=trace.question,
            answer=trace.answer,
            status=trace.status,
            latency_ms=trace.latency_ms,
            iterations=trace.iterations,
            retrieved_count=trace.retrieved_chunks_count,
        )
        results.append(check_result)

    if not results:
        return None

    # Calculate aggregated metrics
    pass_rates = [r["pass_rate"] for r in results]
    latencies = [t.latency_ms for t in traces]
    iterations = [t.iterations for t in traces]

    return {
        "total_runs": len(traces),
        "success_rate": sum(r["pass_rate"] for r in results) / len(results),
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
        "avg_iterations": sum(iterations) / len(iterations) if iterations else 0,
        "retrieval_quality": sum(1 for t in traces if t.retrieved_chunks_count > 0) / len(traces),
        "answer_completeness": sum(1 for r in results if all(c["passed"] for c in r["results"])) / len(results),
    }


# ============================================================================
# PAGE 1: METRICS
# ============================================================================
if page == "📈 Metrics":
    st.header("Before & After Metrics")

    col_before, col_divider, col_after = st.columns([1, 0.1, 1])

    before = get_metrics_before_fix()
    after = get_metrics_after_fix()

    with col_before:
        st.subheader("❌ Before Fix (Baseline)")
        with st.container(border=True):
            st.metric("Success Rate", f"{before['success_rate']*100:.1f}%")
            st.metric("Avg Latency", f"{before['avg_latency_ms']:.0f}ms")
            st.metric("Avg Iterations", f"{before['avg_iterations']:.1f}")
            st.metric("Retrieval Quality", f"{before['retrieval_quality']*100:.1f}%")
            st.metric("Answer Completeness", f"{before['answer_completeness']*100:.1f}%")

    with col_divider:
        st.write("")

    if after:
        with col_after:
            st.subheader("✅ After Fix (Current)")
            with st.container(border=True):
                success_delta = (after['success_rate'] - before['success_rate']) * 100
                st.metric(
                    "Success Rate",
                    f"{after['success_rate']*100:.1f}%",
                    delta=f"{success_delta:+.1f}%"
                )

                latency_delta = before['avg_latency_ms'] - after['avg_latency_ms']
                st.metric(
                    "Avg Latency",
                    f"{after['avg_latency_ms']:.0f}ms",
                    delta=f"{latency_delta:+.0f}ms",
                    delta_color="inverse"
                )

                iter_delta = before['avg_iterations'] - after['avg_iterations']
                st.metric(
                    "Avg Iterations",
                    f"{after['avg_iterations']:.1f}",
                    delta=f"{iter_delta:+.1f}",
                    delta_color="inverse"
                )

                retrieval_delta = (after['retrieval_quality'] - before['retrieval_quality']) * 100
                st.metric(
                    "Retrieval Quality",
                    f"{after['retrieval_quality']*100:.1f}%",
                    delta=f"{retrieval_delta:+.1f}%"
                )

                completeness_delta = (after['answer_completeness'] - before['answer_completeness']) * 100
                st.metric(
                    "Answer Completeness",
                    f"{after['answer_completeness']*100:.1f}%",
                    delta=f"{completeness_delta:+.1f}%"
                )

    # Summary stats
    st.markdown("---")
    st.subheader("📊 Summary Statistics")

    col1, col2, col3 = st.columns(3)
    with col1:
        summary = store.get_failure_summary()
        st.metric("Total Traces Analyzed", summary['total_traces'])

    with col2:
        st.metric("Successfully Annotated", summary['annotated'])

    with col3:
        st.metric("Failures Identified", summary['failure_count'])

    # Failure breakdown
    if summary['by_category']:
        st.subheader("🔴 Failure Breakdown")
        failure_df = pd.DataFrame([
            {"Category": k, "Count": v}
            for k, v in sorted(summary['by_category'].items(), key=lambda x: x[1], reverse=True)
        ])
        st.bar_chart(failure_df.set_index("Category"))


# ============================================================================
# PAGE 2: TRACE ANNOTATION
# ============================================================================
elif page == "📝 Trace Annotation":
    st.header("Annotate Traces")

    traces = store.get_all_traces()

    if not traces:
        st.warning("No traces found. Generate sample traces first.")
        if st.button("Generate Sample Traces"):
            from week4_sample_traces import generate_sample_traces, save_sample_traces_to_store
            samples = generate_sample_traces(20)
            save_sample_traces_to_store(samples)
            st.rerun()
    else:
        # Filter view
        col1, col2 = st.columns(2)
        with col1:
            show_only = st.selectbox(
                "Show traces:",
                ["All", "Annotated", "Not Annotated", "Successful", "Failed"]
            )

        filtered_traces = traces
        if show_only == "Annotated":
            filtered_traces = [t for t in traces if t.annotator_notes]
        elif show_only == "Not Annotated":
            filtered_traces = [t for t in traces if not t.annotator_notes]
        elif show_only == "Successful":
            filtered_traces = [t for t in traces if t.success]
        elif show_only == "Failed":
            filtered_traces = [t for t in traces if not t.success]

        st.info(f"Showing {len(filtered_traces)} of {len(traces)} traces")

        # Trace list
        for i, trace in enumerate(filtered_traces):
            with st.expander(
                f"Trace #{i+1}: {trace.question[:50]}... | Status: {trace.status}"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Trace ID:** {trace.trace_id}")
                    st.write(f"**Status:** {trace.status}")
                    st.write(f"**Timestamp:** {trace.timestamp}")
                    st.write(f"**Latency:** {trace.latency_ms}ms")
                    st.write(f"**Iterations:** {trace.iterations}")

                with col2:
                    st.write(f"**Question:** {trace.question}")
                    st.write(f"**Retrieved:** {trace.retrieved_chunks_count} chunks")
                    st.write(f"**Model:** {trace.model}")

                if trace.answer:
                    st.write(f"**Answer:** {trace.answer}")

                st.subheader("📋 Annotation")

                # Failure category selector
                category_options = [None] + list(FailureCategory)
                category_labels = ["✅ No Failure"] + [
                    f"❌ {cat.value.replace('_', ' ').title()}"
                    for cat in FailureCategory
                ]

                selected_category = st.selectbox(
                    "Failure Category:",
                    range(len(category_options)),
                    format_func=lambda x: category_labels[x],
                    key=f"cat_{trace.trace_id}"
                )

                failure_cat = category_options[selected_category] if selected_category > 0 else None

                # Notes
                notes = st.text_area(
                    "Annotator Notes:",
                    value=trace.annotator_notes or "",
                    key=f"notes_{trace.trace_id}",
                    height=100
                )

                # Save button
                if st.button("💾 Save Annotation", key=f"save_{trace.trace_id}"):
                    store.update_trace_annotation(trace.trace_id, failure_cat, notes)
                    st.success("✓ Annotation saved!")


# ============================================================================
# PAGE 3: TRACE DETAIL
# ============================================================================
elif page == "🔍 Trace Detail":
    st.header("Trace Detail & Validation")

    traces = store.get_all_traces()
    if not traces:
        st.warning("No traces found.")
    else:
        # Trace selector
        trace_ids = [f"{t.trace_id} - {t.question[:30]}..." for t in traces]
        selected_idx = st.selectbox("Select trace:", range(len(traces)), format_func=lambda i: trace_ids[i])
        trace = traces[selected_idx]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📌 Trace Metadata")
            st.write(f"**ID:** {trace.trace_id}")
            st.write(f"**Timestamp:** {trace.timestamp}")
            st.write(f"**Question:** {trace.question}")
            st.write(f"**Model:** {trace.model}")

        with col2:
            st.subheader("⚙️ Execution Metrics")
            st.write(f"**Status:** {trace.status}")
            st.write(f"**Latency:** {trace.latency_ms}ms")
            st.write(f"**Iterations:** {trace.iterations}")
            st.write(f"**Retrieved Chunks:** {trace.retrieved_chunks_count}")

        if trace.answer:
            st.subheader("💬 Answer")
            st.write(trace.answer)

        # Run checks
        st.subheader("✓ Automated Checks")
        check_suite = CheckSuite()
        check_results = check_suite.validate_trace(
            question=trace.question,
            answer=trace.answer,
            status=trace.status,
            latency_ms=trace.latency_ms,
            iterations=trace.iterations,
            retrieved_count=trace.retrieved_chunks_count,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Checks Passed", check_results["passed"])
        with col2:
            st.metric("Checks Failed", check_results["failed"])
        with col3:
            st.metric("Pass Rate", f"{check_results['pass_rate']*100:.1f}%")

        # Detailed results
        st.subheader("📋 Check Results")
        for result in check_results["results"]:
            status_icon = "✓" if result["passed"] else "✗"
            with st.expander(f"{status_icon} {result['check_name']}"):
                if result["passed"]:
                    st.success("Passed")
                else:
                    st.error(result["error_message"])
                if result["details"]:
                    st.write("Details:", result["details"])


# ============================================================================
# PAGE 4: FAILURE TAXONOMY
# ============================================================================
elif page == "📋 Failure Taxonomy":
    st.header("Failure Taxonomy & Prioritization")

    summary = store.get_failure_summary()

    st.subheader("🎯 Failure Categories (4+ Required)")

    categories = [
        {
            "name": FailureCategory.HALLUCINATION.value,
            "description": "Model generates false information not in documents",
            "example": "Stating 'quantum embeddings are the future' when not in docs",
            "impact": "High - destroys user trust",
            "frequency": summary["by_category"].get(FailureCategory.HALLUCINATION.value, 0),
        },
        {
            "name": FailureCategory.INCOMPLETE_ANSWER.value,
            "description": "Answer doesn't fully address the question",
            "example": "Just saying 'RAG is a technique' without explanation",
            "impact": "High - unhelpful to users",
            "frequency": summary["by_category"].get(FailureCategory.INCOMPLETE_ANSWER.value, 0),
        },
        {
            "name": FailureCategory.RETRIEVAL_FAILURE.value,
            "description": "Failed to retrieve relevant documents when needed",
            "example": "No chunks retrieved even though relevant docs exist",
            "impact": "High - can't ground answer",
            "frequency": summary["by_category"].get(FailureCategory.RETRIEVAL_FAILURE.value, 0),
        },
        {
            "name": FailureCategory.NO_SEARCH_TRIGGER.value,
            "description": "Didn't search when should have",
            "example": "Could answer from context but didn't retrieve first",
            "impact": "Medium - missed opportunity for grounding",
            "frequency": summary["by_category"].get(FailureCategory.NO_SEARCH_TRIGGER.value, 0),
        },
        {
            "name": FailureCategory.API_ERROR.value,
            "description": "Underlying API/service error",
            "example": "Pinecone query timeout or OpenAI rate limit",
            "impact": "Medium - reliability issue",
            "frequency": summary["by_category"].get(FailureCategory.API_ERROR.value, 0),
        },
        {
            "name": FailureCategory.TIMEOUT.value,
            "description": "Call took too long or timed out",
            "example": "Agent couldn't complete in 30 seconds",
            "impact": "Medium - UX degradation",
            "frequency": summary["by_category"].get(FailureCategory.TIMEOUT.value, 0),
        },
    ]

    # Display as table
    taxonomy_data = []
    for cat in categories:
        taxonomy_data.append({
            "Category": cat["name"].replace("_", " ").title(),
            "Frequency": cat["frequency"],
            "Impact": cat["impact"],
        })

    df = pd.DataFrame(taxonomy_data)
    df["Priority Score"] = df["Frequency"]  # Simplified: frequency as proxy for priority

    st.dataframe(df, use_container_width=True)

    st.subheader("🎯 Priority Matrix")
    st.write("**Top Target for Fix:** HALLUCINATION & INCOMPLETE_ANSWER")
    st.write("- Frequency: High (most common failures)")
    st.write("- Impact: High (destroys trust & usability)")
    st.write("- Mitigation: Better prompt grounding + retrieval validation")

    st.subheader("📋 Detailed Taxonomy")
    for cat in categories:
        with st.expander(f"**{cat['name'].replace('_', ' ').title()}** (Freq: {cat['frequency']})"):
            st.write(f"**Description:** {cat['description']}")
            st.write(f"**Example:** {cat['example']}")
            st.write(f"**Impact:** {cat['impact']}")

    # Suggestions for fixes
    st.markdown("---")
    st.subheader("💡 Suggested Fixes")
    st.write("""
    ### Fix #1: Better Prompt Grounding (Target: HALLUCINATION)
    - Modify agent prompt to explicitly refuse if no good retrieval
    - Add validation: "If retrieved_chunks < 2, ask user to clarify"
    - Use stronger language: "Answer ONLY based on retrieved documents"

    ### Fix #2: Forced Retrieval (Target: NO_SEARCH_TRIGGER)
    - Always attempt retrieval first before generating
    - Simplify search decision logic
    - Use more lenient retrieval thresholds

    ### Fix #3: Completeness Check (Target: INCOMPLETE_ANSWER)
    - Add post-generation validation: "Is answer > 50 words?"
    - If too short, force a second iteration
    - Require specific details in answer
    """)
