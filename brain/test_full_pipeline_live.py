"""Test the full chat pipeline end-to-end with ConversationalIntelligence."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import generate_response_with_metadata

queries = [
    "How are you feeling right now?",
    "What are you working on?",
    "What have you learned recently?",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {q}")
    print(f"{'='*60}")
    try:
        result = generate_response_with_metadata(q)
        if isinstance(result, dict):
            print(f"Source: {result.get('source', 'unknown')}")
            print(f"Intent: {result.get('intent', 'unknown')}")
            resp = result.get('response', str(result))
            print(f"Response ({len(resp)} chars):")
            print(resp[:500])
        else:
            print(f"Response ({len(str(result))} chars):")
            print(str(result)[:500])
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("\n\nDone.")