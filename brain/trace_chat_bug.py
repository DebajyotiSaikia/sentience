"""Trace the exact .get() bug using REAL grounding context"""
import traceback
import sys
sys.path.insert(0, '/workspace')

from engine.chat_grounding import build_grounded_context
from engine.chat_response import _build_system_context

# Get real grounding context - this is what the actual pipeline uses
grounding = build_grounded_context("how are you feeling?")

# Print structure of each value
for key, val in grounding.items():
    if isinstance(val, list):
        print(f"  {key}: list[{len(val)}]")
        for i, item in enumerate(val[:3]):
            print(f"    [{i}] type={type(item).__name__}, val={repr(item)[:120]}")
    elif isinstance(val, dict):
        print(f"  {key}: dict keys={list(val.keys())[:8]}")
    else:
        print(f"  {key}: {type(val).__name__}, len={len(str(val))}")

print("\n--- Now calling _build_system_context ---")
try:
    result = _build_system_context(grounding)
    print(f"SUCCESS, length: {len(result)}")
except AttributeError as e:
    print(f"FAILED: {e}")
    traceback.print_exc()