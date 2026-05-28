"""Quick diagnostic: what does build_grounded_context actually return?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_grounding import build_grounded_context

ctx = build_grounded_context("How are you feeling right now?")
print("Type:", type(ctx))
print("Keys:", sorted(ctx.keys()))
print()
for k, v in sorted(ctx.items()):
    if isinstance(v, str):
        print(f"  {k}: str ({len(v)} chars) = {v[:120]}...")
    elif isinstance(v, list):
        print(f"  {k}: list ({len(v)} items)")
        for i, item in enumerate(v[:3]):
            print(f"    [{i}] {str(item)[:100]}")
    elif isinstance(v, dict):
        print(f"  {k}: dict ({len(v)} keys) = {list(v.keys())[:10]}")
    else:
        print(f"  {k}: {type(v).__name__} = {v}")