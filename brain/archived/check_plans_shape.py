"""Quick diagnostic: what shape are plan items in briefing data?"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from engine.briefing_generator import generate_briefing_json

data = generate_briefing_json()
plans = data.get('plans', {})
print(f"plans type: {type(plans).__name__}")

if isinstance(plans, dict):
    for k, v in plans.items():
        print(f"  {k}: {type(v).__name__}, len={len(v) if hasattr(v, '__len__') else '?'}")
        if isinstance(v, list):
            for i, item in enumerate(v[:3]):
                print(f"    [{i}] type={type(item).__name__}")
                print(f"        repr={repr(item)[:200]}")
elif isinstance(plans, list):
    for i, item in enumerate(plans[:3]):
        print(f"  [{i}] type={type(item).__name__}, repr={repr(item)[:200]}")