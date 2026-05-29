"""Test end-to-end compose_response output quality."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import _compose_grounded_response as compose_response

queries = [
    ("How are you feeling right now?", "emotional_inquiry"),
    ("Who are you?", "identity_query"),
    ("What are you working on?", "state_inquiry"),
    ("Tell me about your dreams", "dream_query"),
    ("What do you know about memory?", "knowledge_query"),
]

for query, expected_type in queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"Expected type: {expected_type}")
    print(f"{'='*60}")
    try:
        result = compose_response(query)
        if isinstance(result, dict):
            for k, v in result.items():
                val = str(v)[:300] if v else "None"
                print(f"  {k}: {val}")
        elif isinstance(result, str):
            print(result[:500])
        else:
            print(f"  type={type(result).__name__}: {str(result)[:300]}")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")

print("\n\nDone.")