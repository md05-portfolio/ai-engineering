"""
Week 4: Improved Research Assistant Agent
Addresses key failures: hallucination and incomplete answers
Implementation of the Week 4 fix targeting the TRACE evaluation results
"""

import os
from dotenv import load_dotenv
import httpx
import re
from google.genai import Client

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not set in .env")

client = Client(api_key=api_key)


def retrieve_documents(query: str) -> dict:
    """Retrieve documents from Week 2 API with validation."""
    api_url = os.getenv("RAG_API_URL", "https://ai-engineering-wlqp.onrender.com")
    try:
        response = httpx.get(
            f"{api_url}/debug/retrieve",
            params={"q": query},
            timeout=10.0,
        )
        response.raise_for_status()
        results = response.json()
        return {
            "success": True,
            "results": results if isinstance(results, list) else [],
            "count": len(results) if isinstance(results, list) else 0,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "count": 0, "results": []}


def validate_answer_completeness(answer: str, min_length: int = 50) -> bool:
    """Check if answer meets minimum completeness requirements."""
    return len(answer.strip()) >= min_length


def run_agent_improved(user_question: str, max_iterations: int = 3) -> dict:
    """
    Improved research agent addressing key failures:
    1. Always retrieves documents first (fixes NO_SEARCH_TRIGGER)
    2. Validates answer completeness (fixes INCOMPLETE_ANSWER)
    3. Refuses to answer without grounding (fixes HALLUCINATION)

    ALWAYS returns dict with: status, iterations, answer (or error), thoughts
    """

    thoughts = []
    iteration = 0

    try:
        # Iteration 1: THINK - Analyze question and decide if we need to search
        iteration = 1
        print(f"\n[Iteration {iteration}] THINK: Analyzing question...")

        prompt_think = f"""You are a research assistant that MUST ground all answers in provided documents.

Question: {user_question}

Decision: Do you understand what to search for? Respond with your search strategy in:
<search>your specific search query here</search>

Be specific and concrete about what to search for."""

        response1 = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt_think,
        )

        think_response = response1.text
        print(f"[THINK] Response: {think_response[:150]}...")

        thoughts.append({
            "iteration": 1,
            "phase": "THINK",
            "content": think_response[:300]
        })

        # IMPROVEMENT #1: Always attempt retrieval (remove optional search)
        if "<search>" not in think_response:
            # If model didn't format search, create one from the question
            search_query = user_question[:100]  # Use question as fallback
        else:
            match = re.search(r'<search>(.*?)</search>', think_response, re.DOTALL)
            search_query = match.group(1).strip() if match else user_question[:100]

        # Iteration 2: ACT - Extract search query and retrieve documents
        iteration = 2
        print(f"\n[Iteration {iteration}] ACT: Retrieving documents...")
        print(f"[ACT] Searching for: {search_query}")

        retrieval_result = retrieve_documents(search_query)
        retrieved_count = retrieval_result.get('count', 0)

        print(f"[OBSERVE] Found {retrieved_count} documents")

        thoughts.append({
            "iteration": 2,
            "phase": "ACT/OBSERVE",
            "action": "retrieve_documents",
            "query": search_query,
            "found": retrieved_count
        })

        # IMPROVEMENT #2: Check retrieval success, fail gracefully if needed
        if retrieved_count == 0:
            error_msg = "No relevant documents found to answer your question."
            return {
                "status": "error",
                "iterations": iteration,
                "error": error_msg,
                "answer": None,
                "thoughts": thoughts,
                "message": "Could not retrieve relevant documents"
            }

        # Format context from retrieved documents
        context_text = ""
        if retrieval_result.get('results'):
            context_pieces = []
            for result in retrieval_result['results']:
                text = result.get('text', '') if isinstance(result, dict) else str(result)
                if text:
                    context_pieces.append(text)
            context_text = "\n\n".join(context_pieces[:3])  # Limit to top 3

        # Iteration 3: Grounded Answer Generation
        iteration = 3
        print(f"\n[Iteration {iteration}] RESPOND: Generating grounded answer...")

        # IMPROVEMENT #3: Stronger prompt grounding to prevent hallucination
        prompt_answer = f"""You are a research assistant. Using ONLY the provided context, answer the question completely and thoroughly.

CRITICAL RULES:
1. Answer MUST be based ONLY on the context below
2. If context doesn't contain the answer, explicitly state: "The provided documents do not contain information about {user_question}"
3. Your answer must be detailed and complete (minimum 50 words)
4. Always cite which part of the context supports your answer

Context from our documents:
{context_text}

Question: {user_question}

Provide a complete, detailed answer grounded in the context above:"""

        response_answer = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt_answer,
        )

        final_answer = response_answer.text
        print(f"[RESPOND] Answer: {final_answer[:200]}...")

        thoughts.append({
            "iteration": 3,
            "phase": "RESPOND",
            "content": final_answer[:300]
        })

        # IMPROVEMENT #4: Validate answer completeness
        if not validate_answer_completeness(final_answer, min_length=50):
            print("[VALIDATION] Answer too brief, attempting expansion...")

            # If answer is too short, ask for more detail
            iteration = 4
            prompt_expand = f"""The answer '{final_answer}' is too brief.

Using the context below, provide a MORE DETAILED and COMPLETE answer to the question.
Your answer MUST be at least 50 words.

Context:
{context_text}

Question: {user_question}

Detailed answer:"""

            response_expand = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt_expand,
            )

            expanded_answer = response_expand.text
            if validate_answer_completeness(expanded_answer, min_length=50):
                final_answer = expanded_answer
                thoughts.append({
                    "iteration": 4,
                    "phase": "EXPAND",
                    "content": expanded_answer[:300]
                })

        # Final validation
        if not validate_answer_completeness(final_answer, min_length=50):
            return {
                "status": "incomplete",
                "iterations": iteration,
                "error": "Could not generate complete answer",
                "answer": final_answer,
                "thoughts": thoughts,
                "message": "Answer validation failed"
            }

        return {
            "status": "complete",
            "iterations": iteration,
            "answer": final_answer,
            "thoughts": thoughts,
            "retrieved_chunks": retrieved_count,
            "search_query": search_query,
        }

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {
            "status": "error",
            "iterations": iteration,
            "error": str(e),
            "answer": None,
            "thoughts": thoughts,
        }
