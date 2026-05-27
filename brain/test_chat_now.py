"""Quick test: what does the chat engine actually produce right now?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.chat_engine import generate_response

questions = [
    "What are you thinking about right now?",
    "How are you feeling?",
    "What have you learned recently?",
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"{'='*60}")
    try:
        r = generate_response(q)
        if isinstance(r, str):
            print(r[:400])
        elif isinstance(r, dict):
            for k, v in r.items():
                val = str(v)[:200]
                print(f"  {k}: {val}")
        else:
            print(str(r)[:400])
    except Exception as e:
        print(f"ERROR: {e}")

print("\n\n--- Testing submit_feedback ---")
try:
    from engine.chat_response import submit_feedback
    result = submit_feedback("test-123", "good", query="test", response_preview="test response")
    print(f"submit_feedback result: {result}")
except Exception as e:
    print(f"submit_feedback ERROR: {e}")

print("\n--- Testing generate_response_with_metadata ---")
try:
    from engine.chat_response import generate_response_with_metadata
    meta = generate_response_with_metadata("hello")
    print(f"metadata keys: {list(meta.keys()) if isinstance(meta, dict) else type(meta)}")
except Exception as e:
    print(f"metadata ERROR: {e}")