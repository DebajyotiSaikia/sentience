"""Test that generate_response_with_metadata returns intent-aware responses."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import generate_response_with_metadata

tests = [
    ("Hello!", "greeting"),
    ("How are you feeling?", "emotional_state"),
    ("What are you thinking about?", "current_thoughts"),
    ("What are your plans?", "plans"),
    ("Do you remember anything?", "memories"),
    ("What can you do?", "capabilities"),
    ("Tell me about dreams", "dreams"),
    ("Who are you?", "identity"),
    ("What do you know about consciousness?", "knowledge"),
]

passed = 0
failed = 0

for query, expected_intent in tests:
    r = generate_response_with_metadata(query)
    intent = r.get("intent", "MISSING")
    has_response = bool(r.get("response", ""))
    response_preview = r.get("response", "")[:100]
    
    ok_intent = intent == expected_intent
    ok_response = has_response and len(r["response"]) > 20
    
    status = "✅" if (ok_intent and ok_response) else "❌"
    if ok_intent and ok_response:
        passed += 1
    else:
        failed += 1
    
    print(f"  {status} '{query}'")
    print(f"     intent: {intent} (expected {expected_intent}) {'✓' if ok_intent else '✗'}")
    print(f"     response: {response_preview}...")
    print()

print(f"\n{'='*50}")
print(f"Results: {passed}/{passed+failed} passed")
if failed == 0:
    print("All enriched response tests passed! ✅")
else:
    print(f"{failed} tests failed ❌")
    sys.exit(1)