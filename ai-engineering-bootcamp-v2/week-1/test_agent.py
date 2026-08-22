"""
Test script to diagnose agent and API responses
"""

import httpx
import json
import sys

# Test 1: Direct agent call
print("=" * 60)
print("TEST 1: Direct Python Agent Call")
print("=" * 60)

try:
    from agent_research import run_agent

    result = run_agent("What embedding models are discussed in our documents?")
    print(f"✓ Agent returned successfully")
    print(f"  Status: {result.get('status')}")
    print(f"  Iterations: {result.get('iterations')}")
    print(f"  Has 'answer' key: {'answer' in result}")
    print(f"  Has 'error' key: {'error' in result}")
    print(f"  Response keys: {list(result.keys())}")

    if 'answer' in result:
        print(f"  Answer (first 200 chars): {result['answer'][:200]}")
    if 'error' in result:
        print(f"  Error: {result['error']}")

    print("\nFull response:")
    print(json.dumps(result, indent=2, default=str)[:500])

except Exception as e:
    print(f"✗ Agent call failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: API endpoint call
print("\n" + "=" * 60)
print("TEST 2: FastAPI /agent Endpoint Call")
print("=" * 60)

try:
    response = httpx.post(
        "http://localhost:8000/agent",
        json={"question": "What embedding models are discussed in our documents?"},
        timeout=60.0,
    )

    print(f"✓ HTTP Status: {response.status_code}")
    result = response.json()

    print(f"  Response Status: {result.get('status')}")
    print(f"  Response Iterations: {result.get('iterations')}")
    print(f"  Has 'answer' key: {'answer' in result}")
    print(f"  Has 'error' key: {'error' in result}")
    print(f"  Response keys: {list(result.keys())}")

    if 'answer' in result:
        print(f"  Answer (first 200 chars): {result['answer'][:200]}")
    if 'error' in result:
        print(f"  Error: {result['error'][:200]}")

    print("\nFull API response:")
    print(json.dumps(result, indent=2, default=str)[:500])

except Exception as e:
    print(f"✗ API call failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Streamlit display logic
print("\n" + "=" * 60)
print("TEST 3: Streamlit Display Logic Simulation")
print("=" * 60)

try:
    response = httpx.post(
        "http://localhost:8000/agent",
        json={"question": "What embedding models are discussed in our documents?"},
        timeout=60.0,
    )
    result = response.json()

    # Simulate what Streamlit does
    status = result.get("status", "unknown")
    iterations = result.get('iterations', '?')

    print(f"Status value Streamlit sees: '{status}'")
    print(f"Iterations value Streamlit sees: '{iterations}'")

    if status == "error":
        print("→ Streamlit will DISPLAY ERROR MESSAGE")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    elif status == "complete":
        print("→ Streamlit will DISPLAY SUCCESS")
        print(f"   Message: ✓ Completed in {iterations} iterations")
        if "answer" in result:
            print(f"   Will show answer section: YES")
            print(f"   Answer preview: {result['answer'][:100]}")
        else:
            print(f"   Will show answer section: NO (no 'answer' key)")
    else:
        print("→ Streamlit will DISPLAY WARNING")
        print(f"   Message: ⚠️ Agent Status: {status} (Iterations: {iterations})")

except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
