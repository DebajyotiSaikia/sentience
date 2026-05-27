"""Quick end-to-end test of the chat pipeline."""
import json
import sys

# Test the full pipeline
from engine.chat_response import generate_response_with_metadata

test_queries = [
    "How are you feeling right now?",
    "What are you thinking about?",
    "What plans do you have?",
    "What do you know about consciousness?",
    "Hello!",
]

all_ok = True
for q in test_queries:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    try:
        result = generate_response_with_metadata(q)
        resp = result.get('response', '')
        intent = result.get('intent', '?')
        grounding = result.get('grounding', {})
        ms = result.get('processing_ms', '?')
        
        print(f"Intent: {intent}")
        print(f"Response ({len(resp)} chars): {resp[:200]}")
        print(f"Grounding keys: {list(grounding.keys()) if isinstance(grounding, dict) else grounding}")
        print(f"Time: {ms}ms")
        
        # Basic quality checks
        if not resp or len(resp) < 10:
            print("FAIL: Response too short")
            all_ok = False
        elif 'knowledge nodes' in resp.lower() and 'edges' in resp.lower():
            print("WARN: Response looks like raw stats, not conversational")
        else:
            print("OK")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback; traceback.print_exc()
        all_ok = False

print(f"\n{'='*60}")
print("ALL PASSED" if all_ok else "SOME FAILED")
sys.exit(0 if all_ok else 1)