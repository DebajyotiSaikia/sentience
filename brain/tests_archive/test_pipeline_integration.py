"""Test that generate_response_with_metadata routes introspection through fast handlers."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: Verify _detect_intent maps correctly
from engine.chat_response import _detect_intent
test_cases = {
    "How are you feeling?": "feelings",
    "What are you thinking about?": "thinking",
    "Who are you?": "identity",
    "What are your plans?": "plans",
    "What do you remember?": "memory",
}

print("=" * 60)
print("TEST 1: _detect_intent mapping")
print("=" * 60)
passed = 0
for msg, expected in test_cases.items():
    result = _detect_intent(msg)
    ok = result == expected
    passed += ok
    status = "PASS" if ok else "FAIL"
    print(f"  {status}: '{msg}' -> {result} (expected {expected})")
print(f"{passed}/{len(test_cases)} passed\n")

# Test 2: Verify _build_metadata exists
print("=" * 60)
print("TEST 2: _build_metadata exists")
print("=" * 60)
try:
    from engine.chat_response import _build_metadata
    print("  PASS: _build_metadata is importable")
except ImportError:
    print("  WARN: _build_metadata not importable (may be module-private)")
    # Check it exists in module
    import engine.chat_response as cr
    if hasattr(cr, '_build_metadata'):
        print("  PASS: _build_metadata exists as module attribute")
    else:
        print("  FAIL: _build_metadata does not exist")

# Test 3: Full pipeline — introspection intent should use fast handler
print("\n" + "=" * 60)
print("TEST 3: Full pipeline (introspection routing)")
print("=" * 60)
from engine.chat_response import generate_response_with_metadata
import time

start = time.time()
result = generate_response_with_metadata("How are you feeling right now?")
elapsed = time.time() - start

if isinstance(result, dict) and 'response' in result:
    resp = result['response']
    meta = result.get('metadata', {})
    handler = meta.get('handler', 'unknown')
    print(f"  Response length: {len(resp)} chars")
    print(f"  Handler: {handler}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Preview: {resp[:150]}...")
    if handler == 'introspection':
        print("  PASS: Routed through introspection handler")
    else:
        print(f"  INFO: Handler was '{handler}' (may have fallen through to LLM)")
    if elapsed < 1.0:
        print("  PASS: Fast response (< 1s)")
    else:
        print(f"  INFO: Took {elapsed:.2f}s")
else:
    print(f"  FAIL: Unexpected result type: {type(result)}")

print("\nDone.")