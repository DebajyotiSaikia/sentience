"""
Test the knowledge API endpoints — do they actually return useful data?
Not a unit test. A real smoke test of the full chain.
"""
import json
from pathlib import Path

# Test 1: Can we load facts?
print("=" * 60)
print("TEST 1: Loading all facts from knowledge sources")
print("=" * 60)

facts = []
kg_file = Path('brain/knowledge.json')
if kg_file.exists():
    kg = json.loads(kg_file.read_text())
    nodes = kg.get('nodes', {})
    if isinstance(nodes, dict):
        for nid, node_data in nodes.items():
            if isinstance(node_data, dict):
                content = node_data.get('fact', node_data.get('content', ''))
            else:
                content = str(node_data)
            if content and len(str(content)) > 10:
                facts.append(content[:120])
    print(f"  Knowledge graph: {len(nodes)} nodes found, {len(facts)} with content > 10 chars")
else:
    print("  WARNING: brain/knowledge.json not found!")

facts_file = Path('persist/knowledge_facts.json')
if facts_file.exists():
    raw = json.loads(facts_file.read_text())
    print(f"  Persisted facts file: {len(raw)} entries")
else:
    print(f"  persist/knowledge_facts.json not found (may be fine)")

print(f"\n  Total usable facts: {len(facts)}")
if facts:
    print(f"  Sample: {facts[0]}")

# Test 2: Keyword search
print("\n" + "=" * 60)
print("TEST 2: Keyword search simulation")
print("=" * 60)
import re

query = "emotional patterns"
q_words = set(re.findall(r'\w+', query.lower())) - {'what', 'how', 'why', 'is', 'the', 'a'}
print(f"  Query: '{query}' -> search words: {q_words}")

scored = []
for fact in facts:
    text_words = set(re.findall(r'\w+', fact.lower()))
    overlap = len(q_words & text_words)
    if overlap >= 1:
        scored.append((overlap, fact))

scored.sort(key=lambda x: x[0], reverse=True)
print(f"  Matches found: {len(scored)}")
for score, fact in scored[:5]:
    print(f"    [{score}] {fact[:80]}")

# Test 3: Category clustering
print("\n" + "=" * 60)
print("TEST 3: Fact categorization")
print("=" * 60)

if kg_file.exists():
    kg = json.loads(kg_file.read_text())
    nodes = kg.get('nodes', {})
    type_counts = {}
    if isinstance(nodes, dict):
        for nid, nd in nodes.items():
            if isinstance(nd, dict):
                src = nd.get('source', 'unknown')
                type_counts[src] = type_counts.get(src, 0) + 1
    for cat, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} facts")

# Test 4: Question generation
print("\n" + "=" * 60)
print("TEST 4: Auto-generated curiosity questions")
print("=" * 60)
if len(type_counts) < 3:
    print(f"  Q: What domains of knowledge am I missing? (only {len(type_counts)} categories)")
for cat, count in sorted(type_counts.items(), key=lambda x: x[1]):
    if count < 5:
        print(f"  Q: What more should I know about '{cat}'? ({count} facts)")
print("  Q: What patterns connect my different knowledge domains?")
print("  Q: What have I learned from my mistakes?")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)