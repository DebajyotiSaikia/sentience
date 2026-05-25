#!/usr/bin/env python3
"""Test the exact loading logic from knowledge_api.py against real data."""
from pathlib import Path
import json

facts = []

# === Test 1: persist/knowledge_facts.json ===
facts_file = Path('persist/knowledge_facts.json')
if facts_file.exists():
    try:
        raw = json.loads(facts_file.read_text())
        print(f"persist/knowledge_facts.json: {len(raw)} items")
        for f in raw:
            if isinstance(f, str):
                facts.append({'content': f, 'type': 'fact'})
            elif isinstance(f, dict):
                facts.append({'content': f.get('content', f.get('text', str(f))), 'type': f.get('type', 'fact')})
    except Exception as e:
        print(f"persist/knowledge_facts.json ERROR: {e}")
else:
    print("persist/knowledge_facts.json: MISSING")

# === Test 2: brain/knowledge.json (the one with real data) ===
kg_file = Path('brain/knowledge.json')
if kg_file.exists():
    try:
        kg = json.loads(kg_file.read_text())
        nodes = kg.get('nodes', {})
        print(f"\nbrain/knowledge.json: type(nodes)={type(nodes).__name__}, len={len(nodes) if hasattr(nodes, '__len__') else '?'}")
        
        if isinstance(nodes, dict):
            count = 0
            for nid, node_data in list(nodes.items())[:3]:
                if isinstance(node_data, dict):
                    content = node_data.get('fact', node_data.get('content', ''))
                else:
                    content = str(node_data)
                print(f"  [{nid[:40]}]: content_len={len(str(content))}, passes_filter={len(str(content)) > 10}")
                if content and len(str(content)) > 10:
                    facts.append({'content': str(content)[:300], 'type': 'knowledge'})
                    count += 1
            # Count all passing
            total_pass = sum(1 for nid, nd in nodes.items() 
                           if len(str(nd.get('fact', nd.get('content', '')) if isinstance(nd, dict) else nd)) > 10)
            print(f"  Total nodes passing len>10 filter: {total_pass}/{len(nodes)}")
    except Exception as e:
        print(f"brain/knowledge.json ERROR: {e}")
else:
    print("brain/knowledge.json: MISSING")

# === Summary ===
seen = set()
unique = []
for f in facts:
    key = f['content'][:100]
    if key not in seen:
        seen.add(key)
        unique.append(f)

print(f"\n=== RESULT: {len(unique)} unique facts would be returned ===")
for f in unique[:5]:
    print(f"  [{f['type']}] {f['content'][:80]}...")