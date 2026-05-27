"""Test what the chat engine actually produces for different queries."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_engine import generate_response, classify_intent

test_queries = [
    "What are you feeling right now?",
    "What are you working on?",
    "What do you remember recently?",
    "Tell me something you know.",
    "How many knowledge nodes do you have?",
    "Hello!",
    "What makes you curious?",
]

print("=== Intent Classification ===")
for q in test_queries:
    intent = classify_intent(q)
    print(f"  [{intent:12s}] {q}")

print("\n=== Response Generation ===")
for q in test_queries:
    try:
        resp = generate_response(q)
        # Show first 200 chars
        preview = resp[:200] if isinstance(resp, str) else str(resp)[:200]
        print(f"\nQ: {q}")
        print(f"A: {preview}")
        if len(str(resp)) > 200:
            print(f"   ... ({len(str(resp))} chars total)")
    except Exception as e:
        print(f"\nQ: {q}")
        print(f"ERROR: {type(e).__name__}: {e}")

print("\nDone.")