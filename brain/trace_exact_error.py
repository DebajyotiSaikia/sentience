"""Trace the exact location of the .get() error in _build_system_context"""
import traceback
import sys
sys.path.insert(0, '/workspace')

from engine.chat_grounding import build_grounded_context
from engine.chat_response import _build_system_context
ctx = build_grounded_context("How are you feeling?")
ctx = build_grounding_context("How are you feeling?")
print(f"Context keys: {list(ctx.keys())}")

# Check each context value type
for k, v in ctx.items():
    vtype = type(v).__name__
    if isinstance(v, list) and v:
        item_types = set(type(i).__name__ for i in v)
        print(f"  {k}: list[{len(v)}] item_types={item_types}")
        # Show first item if string
        for i, item in enumerate(v[:3]):
            if isinstance(item, str):
                print(f"    [{i}] str: {item[:80]}")
            elif isinstance(item, dict):
                print(f"    [{i}] dict keys: {list(item.keys())}")
    else:
        print(f"  {k}: {vtype} = {str(v)[:80]}")

print("\nNow calling _build_system_context...")
try:
    result = _build_system_context(ctx, "How are you feeling?", "emotional_state")
    print(f"SUCCESS! Length: {len(result)}")
except Exception as e:
    print(f"\nERROR: {e}")
    traceback.print_exc()