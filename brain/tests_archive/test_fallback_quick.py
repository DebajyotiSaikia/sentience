"""Quick test: does generate_response_with_metadata fall back gracefully when no LLM is available?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import generate_response_with_metadata

queries = [
    "What are you thinking about?",
    "How do you feel?",
    "What are your plans?",
    "Who are you?",
]

print("=== Fallback Pipeline Test ===")
for q in queries:
    print(f"\nQuery: {q}")
    try:
        r = generate_response_with_metadata(q)
        if isinstance(r, dict):
            resp = r.get('response', 'NONE')
            print(f"  Status: OK ({len(resp)} chars)")
            print(f"  Preview: {resp[:150]}")
            print(f"  Keys: {list(r.keys())}")
        else:
            print(f"  Got non-dict: {str(r)[:100]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n=== DONE ===")