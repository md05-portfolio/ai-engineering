"""
Week 3: Research Assistant Agent - SIMPLIFIED
Minimal agent that reliably implements Think → Act → Observe
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
    """Retrieve documents from Week 2 API."""
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


def run_agent(user_question: str, max_iterations: int = 3) -> dict:
    """
    Simple research agent with Think → Act → Observe loop.

    ALWAYS returns dict with: status, iterations, answer (or error), thoughts
    """

    thoughts = []
    iteration = 0

    try:
        # Iteration 1: THINK - Analyze question and decide if we need to search
        iteration = 1
        print(f"\n[Iteration {iteration}] THINK: Analyzing question...")

        prompt_think = f"""You are a research assistant. Answer this question, and if you need to search our documents, write:
<search>your search query</search>

Question: {user_question}

Decide: Do you need to search, or can you provide a general answer?"""

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

        # Check if search is needed
        if "<search>" in think_response and "</search>" in think_response:
            # Iteration 2: ACT - Extract search query and retrieve documents
            iteration = 2
            print(f"\n[Iteration {iteration}] ACT: Extracting search query...")

            match = re.search(r'<search>(.*?)</search>', think_response, re.DOTALL)
            if match:
                search_query = match.group(1).strip()
                print(f"[ACT] Searching for: {search_query}")

                # Retrieve documents
                retrieval_result = retrieve_documents(search_query)

                print(f"[OBSERVE] Found {retrieval_result['count']} documents")

                thoughts.append({
                    "iteration": 2,
                    "phase": "ACT/OBSERVE",
                    "action": "retrieve_documents",
                    "query": search_query,
                    "found": retrieval_result['count']
                })

                # Iteration 3: THINK again with search results
                iteration = 3
                print(f"\n[Iteration {iteration}] THINK: Generating answer with search results...")

                results_text = ""
                if retrieval_result['success'] and retrieval_result['count'] > 0:
                    for i, item in enumerate(retrieval_result['results'][:3], 1):
                        if isinstance(item, dict):
                            content = item.get('content', str(item))[:150]
                        else:
                            content = str(item)[:150]
                        results_text += f"{i}. {content}\n"
                else:
                    results_text = "No documents found."

                prompt_answer = f"""Based on these search results, answer the original question.

Question: {user_question}

Search results for '{search_query}':
{results_text}

Provide your answer:"""

                response3 = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt_answer,
                )

                final_answer = response3.text
                print(f"[THINK] Final answer: {final_answer[:150]}...")

                thoughts.append({
                    "iteration": 3,
                    "phase": "THINK",
                    "content": final_answer[:300]
                })

                return {
                    "status": "complete",
                    "answer": final_answer,
                    "iterations": iteration,
                    "thoughts": thoughts,
                }
        else:
            # No search needed - provide answer based on general knowledge
            print(f"\n[No search needed] Providing answer from general knowledge...")

            return {
                "status": "complete",
                "answer": think_response,
                "iterations": 1,
                "thoughts": thoughts,
            }

    except Exception as e:
        print(f"[ERROR] Agent failed: {str(e)}")
        return {
            "status": "error",
            "error": f"Agent failed: {str(e)}",
            "iterations": iteration,
            "thoughts": thoughts,
        }


if __name__ == "__main__":
    result = run_agent("What embedding models are discussed in our documents?")
    print(f"\n\nRESULT:")
    print(f"Status: {result['status']}")
    print(f"Iterations: {result['iterations']}")
    if "answer" in result:
        print(f"Answer: {result['answer'][:200]}")
