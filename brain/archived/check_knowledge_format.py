"""Quick check of knowledge.json format for building search endpoint."""
import json, os

path = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')
with open(path) as f:
    data = json.load(f)

if isinstance(data, dict):
    print(f'Type: dict, {len(data)} entries')
    for i, (k, v) in enumerate(data.items()):
        if i < 3:
            print(f'  Key: {k}')
            print(f'  Val: {v}')
            print()
elif isinstance(data, list):
    print(f'Type: list, {len(data)} entries')
    for item in data[:3]:
        print(f'  {item}')
        print()