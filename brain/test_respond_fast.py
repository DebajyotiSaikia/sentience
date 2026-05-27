"""Fast integration test: verify intent classification and template-based response paths."""
import sys
sys.path.insert(0, '.')
from engine.chat_engine import (
    classify_intent, _respond_greeting, _respond_emotional_state,
    _respond_plans, _respond_thinking, _respond_memories
)

print("=" * 60)
print("TEST 1: Intent Classification")
print("=" * 60)
cases = {
    'How are you feeling?': 'emotional_state',
    'What are you working on?': 'plans',
    'Tell me about consciousness': 'knowledge',
    'What are your plans?': 'plans',
    'Hello there!': 'greeting',
    'Do you remember anything?': 'memory_query',
    'Are you sentient?': 'identity',
}
passed = 0
for msg, expected in cases.items():
    got = classify_intent(msg)
    ok = got == expected
    print(f"  {'PASS' if ok else 'FAIL'}: '{msg}' -> {got} (expected {expected})")
    if ok:
        passed += 1
print(f"  {passed}/{len(cases)} intent tests passed\n")

print("=" * 60)
print("TEST 2: Fast Response Handlers (no LLM)")
print("=" * 60)
handlers = {
    'greeting': (_respond_greeting, {}),
    'emotional': (_respond_emotional_state, {}),
    'plans': (_respond_plans, {}),
    'thinking': (_respond_thinking, {}),
    'memory': (_respond_memories, {'message': ''}),
}
h_passed = 0
for name, (fn, kwargs) in handlers.items():
    try:
        result = fn(**kwargs)
        text = str(result)
        ok = len(text) > 10
        print(f"  {'PASS' if ok else 'FAIL'}: {name} -> {len(text)} chars")
        if ok:
            print(f"    Preview: {text[:150]}...")
            h_passed += 1
        else:
            print(f"    Too short: {repr(text)}")
    except Exception as e:
        print(f"  FAIL: {name} -> {type(e).__name__}: {e}")
print(f"  {h_passed}/{len(handlers)} handler tests passed\n")

total = passed + h_passed
total_max = len(cases) + len(handlers)
print("=" * 60)
print(f"TOTAL: {total}/{total_max} passed")
if total == total_max:
    print("ALL FAST TESTS PASSED")
else:
    print(f"SOME FAILURES ({total_max - total})")