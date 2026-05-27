"""Inspect knowledge.json format to understand categorization gap."""
import json, os

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brain', 'knowledge.json')
with open(path) as f:
    data = json.load(f)

print(f"Type: {type(data).__name__}")
if isinstance(data, dict):
    print(f"Total keys: {len(data)}")
    for i, (k, v) in enumerate(data.items()):
        if i >= 5:
            break
        print(f"\nKey: {k}")
        print(f"  Value type: {type(v).__name__}")
        if isinstance(v, dict):
            print(f"  Fields: {list(v.keys())}")
            for fk, fv in v.items():
                print(f"    {fk}: {str(fv)[:120]}")
        else:
            print(f"  Value: {str(v)[:200]}")
elif isinstance(data, list):
    print(f"Total items: {len(data)}")
    for item in data[:5]:
        print(f"\n  {item}")