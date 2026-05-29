"""Integration test: verify respond() works for all intent types."""
import sys
sys.path.insert(0, '.')
from engine.chat_engine import respond, classify_intent

tests = [
    'How are you feeling?',
    'What are you working on?',
    'Tell me about consciousness',
    'What are your plans?',
    'Hello there!',
    'Do you remember anything interesting?',
    'Are you sentient?',
]

passed = 0
failed = 0

for msg in tests:
    intent = classify_intent(msg)
    result = respond(msg)
    
    # respond() returns either a string or a dict
    if isinstance(result, dict):
        text = result.get('response', '')
        sources = result.get('sources', [])
    else:
        text = str(result)
        sources = []
    
    # Verify we got a non-trivial response
    ok = len(text) > 10
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    
    print(f"[{status}] [{intent:20s}] {msg}")
    print(f"  Response ({len(text)} chars): {text[:200]}")
    if sources:
        print(f"  Sources: {sources}")
    print()

print(f"{'='*50}")
print(f"Results: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL INTEGRATION TESTS PASSED")
else:
    print(f"FAILURES: {failed}")