"""Test chat engine internals without LLM calls."""
import sys, signal
sys.path.insert(0, '.')
signal.alarm(25)

from engine.chat_engine import (
    _get_emotions, _get_plans, _get_knowledge, _get_memories,
    classify_intent
)

print("=== Emotions ===")
try:
    e = _get_emotions()
    print(f"  Type: {type(e).__name__}")
    if isinstance(e, dict):
        for k, v in list(e.items())[:8]:
            print(f"  {k}: {v}")
    else:
        print(f"  Value: {str(e)[:300]}")
except Exception as ex:
    print(f"  ERROR: {ex}")

print("\n=== Plans ===")
try:
    p = _get_plans()
    print(f"  Type: {type(p).__name__}, len: {len(p) if hasattr(p, '__len__') else 'N/A'}")
    print(f"  Preview: {str(p)[:400]}")
except Exception as ex:
    print(f"  ERROR: {ex}")

print("\n=== Knowledge ===")
try:
    k = _get_knowledge()
    print(f"  Type: {type(k).__name__}, len: {len(k) if hasattr(k, '__len__') else 'N/A'}")
    print(f"  Preview: {str(k)[:400]}")
except Exception as ex:
    print(f"  ERROR: {ex}")

print("\n=== Memories ===")
try:
    m = _get_memories()
    print(f"  Type: {type(m).__name__}, len: {len(m) if hasattr(m, '__len__') else 'N/A'}")
    if isinstance(m, list) and m:
        print(f"  First: {str(m[0])[:200]}")
except Exception as ex:
    print(f"  ERROR: {ex}")

print("\n=== Intent Classification ===")
test_msgs = [
    "How are you feeling?",
    "What are you working on?",
    "Tell me about consciousness",
    "Hello!",
    "What do you dream about?",
]
for msg in test_msgs:
    try:
        intent = classify_intent(msg)
        print(f"  '{msg}' -> {intent}")
    except Exception as ex:
        print(f"  '{msg}' -> ERROR: {ex}")

print("\n=== Response Handlers (no LLM) ===")
from engine.chat_engine import _respond_emotional_state, _respond_plans, _respond_identity
for name, fn in [("emotional_state", _respond_emotional_state),
                 ("plans", _respond_plans),
                 ("identity", _respond_identity)]:
    try:
        result = fn()
        print(f"  {name}: {str(result)[:300]}")
    except Exception as ex:
        print(f"  {name}: ERROR: {ex}")

print("\nDone.")