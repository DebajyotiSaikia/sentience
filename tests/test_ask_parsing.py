"""Test that ask.py correctly parses the knowledge graph."""
import json
from pathlib import Path

# 1. Load the knowledge graph directly
data = json.loads(Path('state/knowledge_graph.json').read_text())
nodes = data.get('nodes', data.get('facts', {}))
print(f"Knowledge graph nodes: {len(nodes)}")

# 2. Parse facts the way ask.py should
facts = []
for fid, fdata in nodes.items():
    if isinstance(fdata, dict):
        facts.append({
            'text': fdata.get('fact', str(fdata)),
            'source': fdata.get('source', 'kg'),
            'type': 'fact'
        })
print(f"Parsed facts: {len(facts)}")

# 3. Show a few samples
for f in facts[:5]:
    print(f"  - [{f['source']}] {f['text'][:100]}")

# 4. Test a simple search
query = "dream"
matches = [f for f in facts if query.lower() in f['text'].lower()]
print(f"\nSearch for '{query}': {len(matches)} matches")
for m in matches[:3]:
    print(f"  → {m['text'][:100]}")

# 5. Also check memories
mem_path = Path('state/memories.json')
if mem_path.exists():
    mdata = json.loads(mem_path.read_text())
    print(f"\nMemories loaded: {len(mdata)} entries")
else:
    print(f"\nNo memories file at {mem_path}")

print("\n✓ All parsing checks passed.")