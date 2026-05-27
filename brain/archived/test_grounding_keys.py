"""Check what keys get_grounded_context returns so we can fix _build_metadata."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_grounding import build_grounded_context

ctx = build_grounded_context('consciousness')
print('=== Context Keys ===')
for k, v in ctx.items():
    if isinstance(v, list):
        print(f'  {k}: list[{len(v)}]')
        if v:
            print(f'    first item type: {type(v[0]).__name__}')
            if isinstance(v[0], dict):
                print(f'    first item keys: {list(v[0].keys())[:5]}')
            else:
                print(f'    first item: {str(v[0])[:100]}')
    elif isinstance(v, dict):
        print(f'  {k}: dict keys={list(v.keys())[:5]}')
        for sk, sv in list(v.items())[:3]:
            print(f'    {sk}: {str(sv)[:80]}')
    else:
        print(f'  {k}: {type(v).__name__} = {str(v)[:100]}')