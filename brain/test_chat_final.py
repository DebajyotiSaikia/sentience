"""Final comprehensive test of the improved chat engine."""
import sys
sys.path.insert(0, '.')
from engine.chat_engine import generate_response, classify_intent

print("=" * 50)
print("FINAL CHAT ENGINE TEST")
print("=" * 50)

tests = [
    ("How are you feeling?", "feelings"),
    ("What are your plans?", "plans"),
    ("Who are you?", "identity"),
    ("Hello!", "greeting"),
    ("What do you know?", "knowledge"),
    ("Tell me about your memories", "memories"),
    ("What is the meaning of life?", "general"),
]

all_pass = True
for query, expected_intent in tests:
    intent = classify_intent(query)
    response = generate_response(query)
    
    # Basic quality checks
    is_long_enough = len(response) > 20
    not_error = "error" not in response.lower()[:50]
    not_empty = response.strip() != ""
    has_substance = len(response.split()) > 5
    
    passed = all([is_long_enough, not_error, not_empty, has_substance])
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    
    print(f"\n[{status}] '{query}'")
    print(f"  Intent: {intent} (expected: {expected_intent})")
    print(f"  Length: {len(response)} chars, {len(response.split())} words")
    print(f"  Preview: {response[:120]}...")

print("\n" + "=" * 50)
print(f"RESULT: {'ALL TESTS PASS' if all_pass else 'SOME TESTS FAILED'}")
print("=" * 50)