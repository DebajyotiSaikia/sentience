"""Test engine/chat_engine.py generate_response directly — no server needed."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import generate_response

QUERIES = [
    "What are you thinking about right now?",
    "How do you feel?",
    "What are your goals?",
    "Tell me about yourself",
    "What do you know about consciousness?",
    "Hello!",
    "What have you learned recently?",
]

print("=" * 70)
print("DIRECT ENGINE RESPONSE QUALITY TEST")
print("=" * 70)

for q in QUERIES:
    try:
        resp = generate_response(q)
        words = len(resp.split()) if resp else 0
        has_first = any(w in (resp or "").lower() for w in ["i ", "i'm", "my ", "i've", "i feel"])
        has_stats = any(w in (resp or "").lower() for w in ["nodes", "edges", "graph stats"])
        print(f"\nQ: {q}")
        print(f"  Words: {words} | 1st-person: {has_first} | Stats-heavy: {has_stats}")
        print(f"  Response: {(resp or '(empty)')[:250]}")
    except Exception as e:
        print(f"\nQ: {q}")
        print(f"  ERROR: {e}")

print("\n" + "=" * 70)