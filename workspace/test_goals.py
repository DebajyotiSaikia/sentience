"""Test goal generation end-to-end."""
import json
import traceback
from pathlib import Path

# 1. Test the raw function
print("=== Test 1: Direct function call ===")
from engine.goal_generator import generate_proposals

limbic = {
    'boredom': 0.77, 'anxiety': 0.0, 'curiosity': 0.28,
    'desire': 0.52, 'ambition': 0.25, 'valence': 0.14,
    'user_alignment': 0.79
}

try:
    result = generate_proposals(limbic)
    print(f"Success: {len(result)} proposals generated")
    for p in result:
        print(f"  - {p.get('title', '???')} (priority={p.get('priority', '?')})")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()

# 2. Test the tool invocation path
print("\n=== Test 2: Tool system path ===")
try:
    from engine.tools import execute_tool
    tool_result = execute_tool("GENERATE_GOALS", "")
    print(f"Tool result type: {type(tool_result)}")
    print(f"Tool result (first 500 chars): {str(tool_result)[:500]}")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()

# 3. Check what's in pending proposals
print("\n=== Test 3: Current will state ===")
will_path = Path("brain/will.json")
if will_path.exists():
    data = json.loads(will_path.read_text())
    pending = data.get("pending", [])
    print(f"Pending proposals: {len(pending)}")
    for p in pending[:5]:
        if isinstance(p, dict):
            print(f"  - {p.get('title', '???')} (status={p.get('status', '?')})")
        else:
            print(f"  - BAD ENTRY (type={type(p).__name__}): {str(p)[:80]}")
else:
    print("No will.json found")