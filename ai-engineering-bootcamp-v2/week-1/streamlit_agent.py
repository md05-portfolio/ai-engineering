"""Week 3: Research Agent UI with Streamlit"""

import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Week 3 Agent", page_icon="🤖", layout="wide")
st.title("🤖 Week 3: Research Agent")

API_URL = os.getenv("RAG_API_URL", "https://ai-engineering-wlqp.onrender.com")

# Display API info
col1, col2 = st.columns(2)
with col1:
    st.info(f"**Live API:** {API_URL}")
with col2:
    st.success("✓ Agent Status: Ready")

st.markdown("---")

# Input section
st.subheader("📝 Ask a Research Question")
question = st.text_area(
    "Your question:",
    placeholder="Example: What embedding models are discussed in our documents?",
    height=100
)

# Button to run agent
if st.button("🚀 Run Agent", type="primary", use_container_width=True):
    if not question:
        st.error("Please enter a question")
    else:
        with st.spinner("🤔 Agent thinking... This may take a moment..."):
            try:
                response = httpx.post(
                    f"{API_URL}/agent",
                    json={"question": question},
                    timeout=60.0,
                )
                result = response.json()

                # Extract response fields
                status = result.get("status", "unknown")
                iterations = result.get('iterations', '?')

                # Check response status
                if status == "error":
                    st.error(f"❌ Agent Error: {result.get('error', 'Unknown error')}")
                    if "thoughts" in result and result["thoughts"]:
                        st.info(f"Completed {len(result['thoughts'])} thinking steps before error")
                elif status == "complete":
                    # Success message
                    st.success(f"✓ Completed in {iterations} iterations")

                    # Display answer
                    if "answer" in result:
                        st.subheader("📋 Answer")
                        st.write(result["answer"])
                else:
                    # Other statuses (e.g., max_iterations_reached)
                    st.warning(f"⚠️ Agent Status: {status} (Iterations: {iterations})")
                    if "message" in result:
                        st.info(result["message"])
                    if "error" in result:
                        st.error(f"Error details: {result['error']}")

                # Always show thoughts if available for debugging
                if "thoughts" in result and result["thoughts"] and status != "complete":
                    with st.expander("🧠 Agent Thinking Process"):
                        for thought in result["thoughts"]:
                            st.write(f"**Iteration {thought.get('iteration')} - {thought.get('phase')}**")
                            if thought.get('tool'):
                                st.write(f"Tool: {thought['tool']}")
                            if thought.get('query'):
                                st.write(f"Query: {thought['query']}")
                            st.write(thought.get('content', '')[:300])

                # Display thinking process
                if "thoughts" in result:
                    with st.expander("🧠 Agent Thinking (Think → Act → Observe):"):
                        for thought in result["thoughts"]:
                            iteration = thought.get("iteration", "?")
                            phase = thought.get("phase", "?")

                            if phase == "THINK":
                                st.info(
                                    f"**Iteration {iteration} - THINK**\n\n{thought.get('content', '')[:500]}..."
                                )
                            elif phase == "ACT/OBSERVE":
                                tool = thought.get("tool", "unknown")
                                summary = thought.get("result_summary", "")
                                st.success(
                                    f"**Iteration {iteration} - ACT/OBSERVE**\n\nTool: `{tool}`\n\n{summary}"
                                )

            except httpx.TimeoutException:
                st.error("⏱️ Request timed out. The agent took too long to respond.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

st.markdown("---")

# Info section
st.subheader("ℹ️ About This Agent")
st.markdown("""
This is a **research assistant agent** that implements the Think → Act → Observe loop:

1. **THINK**: The model analyzes your question and decides what to do next
2. **ACT**: If needed, it calls the document retrieval tool to search our knowledge base
3. **OBSERVE**: It receives the search results and decides if it needs more info or can answer

**Key Features:**
- ✓ Multi-step reasoning (not just one-shot)
- ✓ Real tool integration (retrieves from Week 2 documents)
- ✓ Bounded iterations (max 8 steps to prevent runaway token use)
- ✓ Visible thinking process (see every step!)

**This is an Agent because:**
The next step depends on the model's observation of search results. If the initial retrieval doesn't answer the question, it can search again with a different query. The behavior is dynamic, not predetermined.
""")
