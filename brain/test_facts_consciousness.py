"""Diagnose why consciousness facts aren't appearing in _get_facts()"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 1. What does brain/knowledge.json actually have?
brain_kg = json.load(open('brain/knowledge.json'))
nodes = brain_kg.get('nodes', {})
print(f"Brain KG: {len(nodes)} nodes (type: {type(nodes).__name__})")
consciousness_nodes = {k: v for k, v in nodes.items() if 'conscious' in str(v).lower()}
print(f"Consciousness nodes in brain KG: {len(consciousness_nodes)}")
for k, v in list(consciousness_nodes.items())[:3]:
    print(f"  {k}: fact='{v.get('fact', 'N/A')[:60]}'")

# 2. What does state/knowledge_graph.json have?
state_kg = json.load(open('state/knowledge_graph.json'))
snodes = state_kg.get('nodes', {})
print(f"\nState KG: {len(snodes)} nodes (type: {type(snodes).__name__})")
if isinstance(snodes, dict):
    sc = {k: v for k, v in snodes.items() if 'conscious' in str(v).lower()}
elif isinstance(snodes, list):
    sc = [n for n in snodes if 'conscious' in str(n).lower()]
else:
    sc = []
print(f"Consciousness nodes in state KG: {len(sc)}")

# 3. What does _get_facts() return?
from engine.chat_engine import _get_facts
facts = _get_facts()
print(f"\n_get_facts() returned: {len(facts)} facts")
c_facts = [f for f in facts if 'conscious' in f.lower()]
print(f"With 'conscious': {len(c_facts)}")

# 4. Show a sample of what _get_facts returns
print("\nSample facts (first 5):")
for f in facts[:5]:
    print(f"  '{f[:80]}'")

# 5. Check if brain KG facts specifically are present
if consciousness_nodes:
    sample_key = list(consciousness_nodes.keys())[0]
    sample_fact = consciousness_nodes[sample_key].get('fact', '')[:30]
    found = any(sample_fact[:20] in f for f in facts) if sample_fact else False
    print(f"\nSample brain consciousness fact '{sample_fact}' found in results: {found}")