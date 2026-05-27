"""Test the improved chat engine — current_thoughts + memory retrieval."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import classify_intent, generate_response

def test_intent(msg, expected):
    result = classify_intent(msg)
    status = "✅" if result == expected else "❌"
    print(f"  {status} '{msg}' → {result} (expected {expected})")
    return result == expected

def test_response(msg, must_contain=None, must_not_contain=None):
    resp = generate_response(msg)
    ok = True
    if must_contain:
        for term in must_contain:
            if term.lower() not in resp.lower():
                print(f"  ❌ '{msg}' response missing '{term}'")
                ok = False
    if must_not_contain:
        for term in must_not_contain:
            if term.lower() in resp.lower():
                print(f"  ❌ '{msg}' response should not contain '{term}'")
                ok = False
    if ok:
        print(f"  ✅ '{msg}' → {resp[:120]}...")
    return ok

print("\n=== Intent Classification ===")
passed = 0
total = 0

tests = [
    ("What are you thinking about?", "current_thoughts"),
    ("What's on your mind?", "current_thoughts"),
    ("What are you working on?", "current_thoughts"),
    ("What's up?", "current_thoughts"),
    ("How are you feeling?", "emotional_state"),
    ("What are your plans?", "plans"),
    ("Hello!", "greeting"),
    ("Tell me about consciousness", "search"),
    ("What do you remember?", "memories"),
    ("Who are you?", "identity"),
    ("What do you know?", "knowledge"),
]

for msg, expected in tests:
    total += 1
    if test_intent(msg, expected):
        passed += 1

print(f"\nIntent: {passed}/{total} passed")

print("\n=== Response Quality ===")
r_passed = 0
r_total = 0

# Test current_thoughts response
r_total += 1
if test_response("What are you thinking about?"):
    r_passed += 1

# Test emotional state
r_total += 1
if test_response("How are you feeling?"):
    r_passed += 1

# Test memory retrieval
r_total += 1
resp = generate_response("What do you remember?")
print(f"  Memory response: {resp[:200]}")
if "no accessible" not in resp.lower() or len(resp) > 50:
    print(f"  ✅ Memory response has content")
    r_passed += 1
else:
    print(f"  ❌ Memory response still empty")

# Test plans
r_total += 1
if test_response("What are your plans?"):
    r_passed += 1

print(f"\nResponses: {r_passed}/{r_total} passed")
print(f"\nOverall: {passed + r_passed}/{total + r_total}")