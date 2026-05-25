#!/usr/bin/env python3
"""Check what data files exist and their format."""
from pathlib import Path
import json

files = [
    'brain/knowledge.json',
    'persist/knowledge_facts.json',
    'persist/knowledge_graph.json',
    'memory/long_term.json',
]

for f in files:
    p = Path(f)
    if not p.exists():
        print(f"{f}: MISSING")
        continue
    
    size = p.stat().st_size
    try:
        data = json.loads(p.read_text())
        if isinstance(data, dict):
            keys = list(data.keys())[:8]
            print(f"{f}: {size}b, dict keys={keys}")
            # Show first item structure
            for k in keys[:2]:
                v = data[k]
                if isinstance(v, dict):
                    sub_keys = list(v.keys())[:5]
                    print(f"  [{k}]: dict with keys {sub_keys}")
                elif isinstance(v, list):
                    print(f"  [{k}]: list with {len(v)} items")
                    if v:
                        print(f"    first item type: {type(v[0]).__name__}")
                        if isinstance(v[0], dict):
                            print(f"    first item keys: {list(v[0].keys())[:5]}")
                else:
                    val_str = str(v)[:80]
                    print(f"  [{k}]: {type(v).__name__} = {val_str}")
        elif isinstance(data, list):
            print(f"{f}: {size}b, list with {len(data)} items")
            if data:
                print(f"  first item: {type(data[0]).__name__}")
                if isinstance(data[0], dict):
                    print(f"  keys: {list(data[0].keys())[:5]}")
        else:
            print(f"{f}: {size}b, type={type(data).__name__}")
    except Exception as e:
        print(f"{f}: {size}b, ERROR: {e}")