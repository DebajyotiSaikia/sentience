"""Trace _search internals to find exactly where data gets lost."""
import json, os, sys

# Step 1: Load data the way ask.py should
kpath = 'brain/knowledge.json'
with open(kpath) as f:
    kg = json.load(f)

nodes = kg.get('nodes', {})
print(f"Raw nodes: {len(nodes)} (type: {type(nodes).__name__})")

# Step 2: Try searching manually — what SHOULD work
query = 'identity'
hits = []
for node_id, node_data in nodes.items():
    text = ''
    if isinstance(node_data, dict):
        text = node_data.get('fact', '')
    elif isinstance(node_data, str):
        text = node_data
    if query.lower() in text.lower():
        hits.append((node_id, text[:80]))

print(f"\nManual search for '{query}': {len(hits)} hits")
for nid, txt in hits[:3]:
    print(f"  [{nid}] {txt}")

# Step 3: Now trace what ask.py actually does
print("\n--- Tracing ask.py internals ---")
import importlib, inspect
from web import ask
src = inspect.getsource(ask._search)
# Find how it loads/searches
lines = src.split('\n')
for i, line in enumerate(lines):
    print(f"  {i:3d}: {line}")

# Step 4: Try calling with debug
print("\n--- Calling _search('identity') ---")
result = ask._search('identity')
print(f"Result: facts={len(result[0])}, mems={len(result[1])}, related={len(result[2])}")