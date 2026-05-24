"""Inspect brain/soul.json structure to map fields for state sync."""
import json

d = json.load(open('brain/soul.json'))
for k, v in d.items():
    if isinstance(v, dict):
        print(f'{k}: dict with keys {list(v.keys())[:10]}')
    elif isinstance(v, list):
        print(f'{k}: list of {len(v)} items')
    else:
        print(f'{k}: {type(v).__name__} = {str(v)[:100]}')