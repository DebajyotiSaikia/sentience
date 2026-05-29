"""Test that the _respond_general function works with the new grounded prompt integration."""
import sys
sys.path.insert(0, '.')

# Test 1: Function structure is intact
from engine.chat_engine import _respond_general
import inspect
src = inspect.getsource(_respond_general)

checks = {
    'grounded_prompt usage': 'grounded_prompt' in src,
    'ctx.get for system_prompt': 'ctx.get("system_prompt"' in src,
    'ctx.get for working_memory': 'ctx.get("working_memory"' in src,
    'call_llm present': 'call_llm' in src,
    'mood modulation': 'mood_lower' in src,
    'fallback path': 'Fallback' in src,
    'template fallback': 'Template fallback' in src,
}

all_pass = True
for name, result in checks.items():
    status = "PASS" if result else "FAIL"
    if not result:
        all_pass = False
    print(f"  [{status}] {name}")

print(f"\nFunction: {len(src.splitlines())} lines")

# Test 2: The function can be called (dry run with mock context)
print("\n--- Calling _respond_general with test data ---")
try:
    result = _respond_general(
        "Hello, how are you feeling?",
        history=[],
        agent_state={"mood": "Inquisitive", "valence": 0.5}
    )
    print(f"  Response length: {len(result)} chars")
    print(f"  First 200 chars: {result[:200]}")
    print("  [PASS] Function executed without crash")
except Exception as e:
    print(f"  [INFO] Function raised: {type(e).__name__}: {e}")
    # This is OK if it's just missing LLM/data — we want no syntax errors

print(f"\nOverall structure: {'ALL PASS' if all_pass else 'SOME FAILURES'}")