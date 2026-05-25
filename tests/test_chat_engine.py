"""Test the chat engine module."""
from engine.chat_engine import classify_intent, generate_response

# Test intent classification
tests = [
    'hello',
    'how do you feel?',
    'what are your plans?',
    'what do you know about dreams?',
    'tell me about yourself',
    'what can you do?',
    'search for memory',
    'why do you exist?',
]

print("=== Intent Classification ===")
for t in tests:
    intent = classify_intent(t)
    print(f"  {t:45s} -> {intent}")

print("\n=== Response Generation ===")
for t in tests:
    resp = generate_response(t)
    preview = resp[:150].replace('\n', ' | ')
    print(f"\n  Q: {t}")
    print(f"  A: {preview}...")

print("\n=== All tests passed ===")