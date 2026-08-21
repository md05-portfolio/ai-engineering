# Week 3 Agent Assignment - Setup & Planning

**Status:** Ready to implement  
**Decisions Locked:** A,A,A,A  
**Date Started:** August 13, 2026  
**Tokens:** Save this file to preserve context for next session

---

## 📚 Context from Week 1 & 2

**Live URLs:**
- API: https://ai-engineering-wlqp.onrender.com
- Streamlit: https://ai-engineering-streamlit.onrender.com
- GitHub: https://github.com/md05-portfolio/ai-engineering/tree/main/ai-engineering-bootcamp-v2/week-1

**Week 2 Completed:**
- `/ask` endpoint (RAG-enhanced)
- `/ingest` endpoint (document ingestion)
- `/debug/retrieve` endpoint (retrieval testing)
- Pinecone vector store (12 vectors indexed)
- 5 sample documents ingested

---

## 🎯 Week 3 Assignment

**Source:** https://tailabs.ai/ai-eng-syllabus/week-3/week-3-agent-assignment-guide/

**What is an Agent?**
- Think → Act → Observe → Decide loop
- Multi-step (not linear like RAG)
- Calls real tools based on observations
- Next step depends on tool results

**vs. Workflow:**
- Workflow: A → B → C always (predetermined)
- Agent: A → (observe) → B or C? (depends on result)

---

## 🔧 Week 3 Implementation Plan

### Decisions Made (A,A,A,A)

| Choice | Selection |
|--------|-----------|
| **Task** | Research-assistant (reuse Week 2 docs) |
| **Tool** | Week 2 `/debug/retrieve` endpoint |
| **Stack** | Google ADK (genai library) |
| **Deployment** | Full Render deployment |

---

### Job Definition Sentence (REQUIRED)

**"When a user asks a research question, the agent should find relevant documents via retrieval, analyze them, and then decide if it needs to search for more specific information or can answer based on what it found."**

This is an **AGENT** because:
- Next step depends on retrieval results (unpredictable)
- May chain multiple tool calls
- Observation determines action

---

## 📋 Implementation Steps

### Step 0: Setup ADK Environment

```bash
# Create venv
python -m venv week3_env
source week3_env/Scripts/activate  # or: week3_env\Scripts\activate on Windows

# Install dependencies
pip install google-genai python-dotenv fastapi uvicorn streamlit httpx
```

**Environment Variables Needed:**
```
GOOGLE_API_KEY=<your-google-api-key>
RAG_API_URL=https://ai-engineering-wlqp.onrender.com
```

### Step 1: Create ADK Agent

**File:** `agent_research.py`

```python
import google.genai as genai
from google.genai import Client
import os
from dotenv import load_dotenv
import httpx
import json

load_dotenv()

# Initialize Genai
client = Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Tool definition: Retrieval
def retrieve_documents(query: str, top_k: int = 5) -> dict:
    """Search for relevant documents using Week 2 retrieval."""
    api_url = os.getenv("RAG_API_URL", "https://ai-engineering-wlqp.onrender.com")
    try:
        response = httpx.get(
            f"{api_url}/debug/retrieve",
            params={"q": query},
            timeout=10.0,
        )
        response.raise_for_status()
        return {
            "status": "success",
            "results": response.json(),
            "query": query,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Define tool for ADK
tools = [
    {
        "name": "retrieve_documents",
        "description": "Search the document database for relevant information. Returns top chunks with similarity scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find relevant documents",
                }
            },
            "required": ["query"],
        },
    }
]


def run_agent(user_question: str, max_iterations: int = 8) -> dict:
    """Run the research agent with Think → Act → Observe loop."""
    
    messages = [
        {
            "role": "user",
            "content": f"Research and answer this question: {user_question}",
        }
    ]
    
    thoughts = []
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        
        # THINK: Get model response
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=messages,
            tools=tools,
        )
        
        print(f"[THINK] Model response: {response.text[:200]}...")
        thoughts.append({
            "iteration": iteration,
            "phase": "THINK",
            "content": response.text,
        })
        
        # Check if model wants to call a tool
        if not response.tool_calls:
            print(f"[OBSERVE] No more tool calls needed. Final answer:")
            print(response.text)
            return {
                "status": "complete",
                "answer": response.text,
                "iterations": iteration,
                "thoughts": thoughts,
            }
        
        # ACT: Execute tool calls
        tool_results = []
        for tool_call in response.tool_calls:
            if tool_call.name == "retrieve_documents":
                print(f"[ACT] Retrieving documents for: {tool_call.args['query']}")
                result = retrieve_documents(tool_call.args["query"])
                tool_results.append({
                    "tool": "retrieve_documents",
                    "query": tool_call.args["query"],
                    "result": result,
                })
                
                # OBSERVE: Add result back to conversation
                print(f"[OBSERVE] Retrieved {len(result.get('results', []))} chunks")
                messages.append({"role": "assistant", "content": response.text})
                messages.append({
                    "role": "user",
                    "content": f"Tool result: {json.dumps(result, indent=2)}"
                })
                thoughts.append({
                    "iteration": iteration,
                    "phase": "ACT/OBSERVE",
                    "tool": "retrieve_documents",
                    "result_summary": f"Found {len(result.get('results', []))} chunks",
                })
    
    return {
        "status": "max_iterations_reached",
        "iterations": iteration,
        "thoughts": thoughts,
    }


# Test
if __name__ == "__main__":
    question = "What embedding models are discussed in our documents?"
    print(f"Agent Question: {question}\n")
    result = run_agent(question)
    print(f"\n\nFinal Result: {result['status']}")
    print(f"Iterations: {result['iterations']}")
```

### Step 2: Add FastAPI Endpoint

**In `main.py`, add:**

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

### Step 3: Create Streamlit UI

**File:** `streamlit_agent.py`

```python
import streamlit as st
import httpx
import os

st.set_page_config(page_title="Week 3 Agent", page_icon="🤖")
st.title("Week 3: Research Agent")

API_URL = os.getenv("RAG_API_URL", "https://ai-engineering-wlqp.onrender.com")

st.markdown(f"**Live API:** `{API_URL}`")

# Input
question = st.text_area("Ask a research question:", placeholder="What embedding models are discussed?")

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
                
                st.success(f"Completed in {result.get('iterations', '?')} iterations")
                
                # Display answer
                if "answer" in result:
                    st.subheader("Answer")
                    st.write(result["answer"])
                
                # Display thoughts
                if "thoughts" in result:
                    with st.expander("Agent Thinking (Think → Act → Observe):"):
                        for thought in result["thoughts"]:
                            st.write(f"**Iteration {thought['iteration']} - {thought['phase']}**")
                            st.write(thought.get("content", "")[:200])
                            
            except Exception as e:
                st.error(f"Error: {str(e)}")
```

---

## 🚀 Next Steps (New Session)

1. **Setup:**
   - [ ] Create `week3_env` virtual environment
   - [ ] Install dependencies (google-genai, httpx, etc.)
   - [ ] Get `GOOGLE_API_KEY` from https://ai.google.dev/

2. **Implement:**
   - [ ] Create `agent_research.py` with agent code above
   - [ ] Add `/agent` endpoint to `main.py`
   - [ ] Create `streamlit_agent.py` UI

3. **Test Locally:**
   - [ ] Start Week 2 API: `uvicorn main:app --port 8000`
   - [ ] Run Streamlit: `streamlit run streamlit_agent.py`
   - [ ] Test with question: "What is semantic search?"

4. **Deploy:**
   - [ ] Push to GitHub
   - [ ] Update Render environment variables
   - [ ] Deploy new `/agent` endpoint
   - [ ] Test live URL

5. **Verification:**
   - [ ] Agent completes multi-step loop (Think → Act → Observe)
   - [ ] Tool calls are logged/visible
   - [ ] Streamlit UI shows agent thinking
   - [ ] Write: "This is an agent because [reasoning]"

---

## 📝 Deliverables Checklist

- [ ] Agent with clear job definition
- [ ] Multi-step loop visible (Think → Act → Observe)
- [ ] Real tool integrated (Week 2 `/debug/retrieve`)
- [ ] Iteration limit enforced (8 steps max)
- [ ] Streamlit UI functional
- [ ] Agent vs. workflow justified (1-liner)
- [ ] Live Render deployment
- [ ] No secrets in code
- [ ] One test task demonstrated

---

## 🔑 Key Points to Remember

**Agent Pattern:**
```
User Question
    ↓
[THINK] Model plans next action
    ↓
[ACT] Calls tool (retrieve_documents)
    ↓
[OBSERVE] Receives tool results
    ↓
Loop? → Next step depends on results
```

**Tool Definition:**
- Name: `retrieve_documents`
- Input: query (string)
- Output: top-5 chunks with scores
- Reuses Week 2 `/debug/retrieve` endpoint

**Iteration Limit:** 8 steps (prevents infinite loops)

---

**Ready to continue in new session!** Copy this file path to reference:
```
C:\Users\madhy\AI-Bootcamp\ai-engineering\ai-engineering-bootcamp-v2\week-1\WEEK3_SETUP.md
```
