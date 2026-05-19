#!/usr/bin/env python3
"""Minimal test: what breaks when we call generate_goals?"""
import sys
import traceback

try:
    from engine.soul import load_soul
    soul = load_soul()
    ls = soul.get('limbic_snapshot', 'MISSING')
    print(f"limbic_snapshot type: {type(ls)}")
    print(f"limbic_snapshot value: {repr(ls)[:300]}")
    print()
    
    if isinstance(ls, str):
        print("BUG FOUND: limbic_snapshot is a string, not a dict!")
        print("Fix: need to json.loads() it or fix the serialization")
    elif isinstance(ls, dict):
        print("limbic_snapshot is a proper dict. Testing goal generation...")
        from engine.goal_generator import tool_generate_goals
        result = tool_generate_goals(ls)
        print(f"Result type: {type(result)}")
        print(f"Result preview: {repr(result)[:500]}")
    else:
        print(f"Unexpected type: {type(ls)}")
        
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()