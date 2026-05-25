"""Quick diagnostic: can ask.py actually find and search my data?"""
import json, os, sys

print("=== Data Path Diagnostics ===")

# Test 1: Knowledge graph
kpath = 'brain/knowledge.json'
print(f"\n1. knowledge.json exists: {os.path.exists(kpath)}")
if os.path.exists(kpath):
    with open(kpath) as f:
        data = json.load(f)
    nodes = data.get('nodes', {})
    edges = data.get('edges', [])
    print(f"   Nodes: {len(nodes)}, Edges: {len(edges)}")
    # Show a sample
    for k, v in list(nodes.items())[:2]:
        fact = v.get('fact', str(v))[:80] if isinstance(v, dict) else str(v)[:80]
        print(f"   Sample: {fact}")

# Test 2: Memories
mpath = 'persist/memories.json'
print(f"\n2. memories.json exists: {os.path.exists(mpath)}")
if os.path.exists(mpath):
    with open(mpath) as f:
        mdata = json.load(f)
    print(f"   Type: {type(mdata).__name__}, Count: {len(mdata)}")
    if isinstance(mdata, list) and mdata:
        sample = mdata[0]
        if isinstance(sample, dict):
            print(f"   Keys: {list(sample.keys())}")
            content = str(sample.get('content', sample.get('text', '')))[:80]
            print(f"   Sample: {content}")

# Test 3: Try importing ask module
print("\n3. Importing web.ask...")
try:
    from web.ask import _search
    facts, mems, related = _search('identity')
    print(f"   Search 'identity': {len(facts)} facts, {len(mems)} memories, {len(related)} related")
    if facts:
        print(f"   Top fact: {str(facts[0])[:80]}")
    if not facts and not mems:
        print("   ⚠ No results — search logic or data loading is broken")
except Exception as e:
    print(f"   Import/search failed: {e}")

# Test 4: Try a broader search
try:
    from web.ask import _search
    facts2, mems2, rel2 = _search('dream')
    print(f"\n   Search 'dream': {len(facts2)} facts, {len(mems2)} memories, {len(rel2)} related")
except Exception as e:
    print(f"   Second search failed: {e}")

print("\n=== Done ===")