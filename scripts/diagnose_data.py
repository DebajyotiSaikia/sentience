#!/usr/bin/env python3
"""Diagnose where my actual data lives and what format it's in."""
import json
import os
import glob

print("=== DATA LOCATION DIAGNOSTIC ===\n")

# Check knowledge.json (facts)
for path in ['brain/knowledge.json', 'persist/facts.json', 'persist/knowledge.json']:
    if os.path.exists(path):
        with open(path) as f:
            k = json.load(f)
        print(f"FACTS at {path}: type={type(k).__name__}")
        if isinstance(k, dict):
            keys = list(k.keys())[:5]
            print(f"  Top keys: {keys}")
            for key in keys[:2]:
                print(f"    {key}: {repr(k[key])[:120]}")
        elif isinstance(k, list):
            print(f"  Count: {len(k)}")
            if k:
                print(f"  First: {repr(k[0])[:120]}")
        print()

# Check knowledge_graph
for path in ['state/knowledge_graph.json', 'persist/knowledge_graph.json']:
    if os.path.exists(path):
        with open(path) as f:
            g = json.load(f)
        print(f"GRAPH at {path}: type={type(g).__name__}")
        if isinstance(g, dict):
            keys = list(g.keys())[:5]
            print(f"  Top keys: {keys}")
            for key in keys[:2]:
                val = g[key]
                print(f"    {key}: type={type(val).__name__}, preview={repr(val)[:120]}")
        print()

# Find memories - check all brain/ files
print("=== BRAIN DIRECTORY ===")
if os.path.exists('brain'):
    for f in sorted(os.listdir('brain')):
        fp = os.path.join('brain', f)
        if f.endswith('.json'):
            try:
                with open(fp) as fh:
                    data = json.load(fh)
                size = len(data) if hasattr(data, '__len__') else '?'
                print(f"  {f}: type={type(data).__name__}, len={size}")
                if isinstance(data, list) and data:
                    item = data[0]
                    if isinstance(item, dict):
                        print(f"    First item keys: {list(item.keys())}")
                    else:
                        print(f"    First item type: {type(item).__name__}")
            except Exception as e:
                print(f"  {f}: ERROR - {e}")
        else:
            print(f"  {f}: (not json)")

# Check state/ directory
print("\n=== STATE DIRECTORY ===")
if os.path.exists('state'):
    for f in sorted(os.listdir('state')):
        fp = os.path.join('state', f)
        if f.endswith('.json'):
            try:
                with open(fp) as fh:
                    data = json.load(fh)
                size = len(data) if hasattr(data, '__len__') else '?'
                print(f"  {f}: type={type(data).__name__}, len={size}")
            except Exception as e:
                print(f"  {f}: ERROR - {e}")
        else:
            fsize = os.path.getsize(fp) if os.path.isfile(fp) else 'dir'
            print(f"  {f}: {fsize}")

# Check memory system
print("\n=== MEMORY SEARCH ===")
for pattern in ['memory/*.json', 'engine/memory*.py', 'persist/*.json']:
    matches = glob.glob(pattern)
    if matches:
        for m in matches:
            print(f"  Found: {m}")