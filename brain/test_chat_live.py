"""Test what the chat engine actually produces right now."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import respond, classify_intent

# Test intent classification
print("=== Intent Classification ===")
test_messages = [
    "How are you feeling?",
    "What are you thinking about?",
    "What are your active plans?",
    "What do you remember recently?",
    "Tell me about yourself",
    "What is consciousness?",
]

for msg in test_messages:
    intent = classify_intent(msg)
    print(f"  [{intent:>12}] {msg}")

# Test actual responses
print("\n=== Response Tests ===")
for msg in test_messages[:4]:
    print(f"\n--- Q: {msg} ---")
    try:
        r = respond(msg)
        if isinstance(r, dict):
            text = r.get("response", r.get("text", str(r)))
            print(f"  Type: dict, keys: {list(r.keys())}")
            print(f"  Response: {text[:400]}")
        else:
            print(f"  Type: {type(r).__name__}")
            print(f"  Response: {str(r)[:400]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nDone.")