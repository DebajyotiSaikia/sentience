"""Test that chat.py's get_current_state reads from the correct path."""
import json
import sys
sys.path.insert(0, '/app')

# 1. Verify the emotional state file exists and is readable
print("=== Test 1: Emotional state file ===")
try:
    with open('state/emotional_state.json') as f:
        data = json.load(f)
    print(f"  OK - loaded {len(data)} keys")
    for k, v in list(data.items())[:5]:
        print(f"    {k}: {v}")
except Exception as e:
    print(f"  FAIL: {e}")

# 2. Verify chat.py's get_current_state works
print("\n=== Test 2: get_current_state() ===")
try:
    from web.chat import get_current_state
    state = get_current_state()
    print(f"  OK - returned {type(state).__name__}")
    if isinstance(state, dict):
        for k, v in list(state.items())[:5]:
            print(f"    {k}: {v}")
    else:
        print(f"  Value: {str(state)[:200]}")
except Exception as e:
    print(f"  FAIL: {e}")

# 3. Verify the path fix is actually in the file
print("\n=== Test 3: Path verification in chat.py ===")
with open('web/chat.py') as f:
    content = f.read()
if 'memory/emotional_state.json' in content:
    print("  FAIL - old broken path still present!")
elif 'state/emotional_state.json' in content:
    print("  OK - correct path found")
else:
    print("  WARN - no emotional_state path found at all")

print("\nAll tests complete.")