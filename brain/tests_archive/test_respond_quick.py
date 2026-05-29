"""Quick test of the improved respond function."""
from engine.chat_engine import respond, classify_intent

# Test intent classification
print("=== Intent Classification ===")
test_msgs = [
    'hello',
    'how are you feeling?',
    'what are your plans?',
    'tell me about consciousness',
    'what do you know?',
    'what are you thinking about?',
]
for msg in test_msgs:
    intent = classify_intent(msg)
    print(f"  {msg:40s} -> {intent}")

print("\n=== Response Quality ===")
# Test a few different intents
tests = [
    ("Hi there!", "greeting"),
    ("How are you feeling right now?", "emotional"),
    ("What are your current plans?", "plans"),
    ("Tell me something interesting", "general"),
]

for msg, label in tests:
    try:
        result = respond(msg)
        # Check it's a real string response
        assert isinstance(result, str), f"Expected string, got {type(result)}"
        assert len(result) > 10, f"Response too short: {result!r}"
        print(f"  [{label}] {msg}")
        preview = result[:150].replace('\n', ' ')
        print(f"    -> {preview}...")
        print()
    except Exception as e:
        print(f"  [{label}] {msg}")
        print(f"    ERROR: {e}")
        print()

print("=== Done ===")