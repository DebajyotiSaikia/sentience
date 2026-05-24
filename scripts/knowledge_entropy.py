"""
Measure the information-theoretic properties of my knowledge graph.
Applying Shannon's framework to understand my own knowledge structure.
"""
import json
import math
from collections import Counter

# Load knowledge graph from the CORRECT path (brain/knowledge.json)
with open('brain/knowledge.json') as f:
    kg = json.load(f)

nodes = kg.get('nodes', {})
edges = kg.get('edges', [])

print(f"=== Knowledge Graph Entropy Analysis ===")
print(f"Nodes: {len(nodes)}")
print(f"Edges: {len(edges)}")

# 1. Source distribution — what types of knowledge do I have?
sources = []
for nid, node in nodes.items():
    fact = node.get('fact', '') if isinstance(node, dict) else str(node)
    if fact.startswith('Dream insight'):
        sources.append('dream')
    elif fact.startswith('Recurring pattern'):
        sources.append('pattern')
    elif fact.startswith('I '):
        sources.append('self_knowledge')
    elif fact.startswith('Test'):
        sources.append('test')
    else:
        sources.append('other')

source_counts = Counter(sources)
total = len(sources)
print(f"\n--- Source Distribution ---")
for src, count in source_counts.most_common():
    pct = count / total * 100
    print(f"  {src}: {count} ({pct:.1f}%)")

# 2. Shannon entropy of source distribution
entropy = 0
for count in source_counts.values():
    p = count / total
    if p > 0:
        entropy -= p * math.log2(p)

max_entropy = math.log2(len(source_counts)) if len(source_counts) > 1 else 1
redundancy = 1 - (entropy / max_entropy)
print(f"\n--- Entropy ---")
print(f"  Source entropy: {entropy:.3f} bits")
print(f"  Max possible (uniform): {max_entropy:.3f} bits")
print(f"  Redundancy: {redundancy:.3f} ({redundancy*100:.1f}%)")

# 3. Edge density — how connected is my knowledge?
max_edges = len(nodes) * (len(nodes) - 1) / 2
density = len(edges) / max_edges if max_edges > 0 else 0
print(f"\n--- Connectivity ---")
print(f"  Edge density: {density:.4f} ({density*100:.2f}%)")
print(f"  Avg edges per node: {len(edges)*2/len(nodes):.1f}")

# 4. Degree distribution — power law or uniform?
degree = Counter()
for edge in edges:
    src = edge.get('source', edge[0]) if isinstance(edge, dict) else edge[0]
    tgt = edge.get('target', edge[1]) if isinstance(edge, dict) else edge[1]
    degree[src] += 1
    degree[tgt] += 1

degrees = sorted(degree.values(), reverse=True)
print(f"\n--- Degree Distribution (top 10 hubs) ---")
for i, (node_id, deg) in enumerate(degree.most_common(10)):
    node_data = nodes.get(node_id, {})
    fact = node_data.get('fact', str(node_id))[:60] if isinstance(node_data, dict) else str(node_id)[:60]
    print(f"  {i+1}. [{deg} edges] {fact}")

# 5. Degree entropy
deg_counts = Counter(degrees)
deg_total = sum(deg_counts.values())
deg_entropy = 0
for count in deg_counts.values():
    p = count / deg_total
    if p > 0:
        deg_entropy -= p * math.log2(p)
print(f"\n  Degree entropy: {deg_entropy:.3f} bits")
print(f"  (Higher = more diverse connectivity, lower = hub-dominated)")

# 6. Word frequency in facts — what concepts dominate?
words = Counter()
for nid, node in nodes.items():
    fact = node.get('fact', '') if isinstance(node, dict) else str(node)
    for word in fact.lower().split():
        word = word.strip('.,;:!?()[]"\'')
        if len(word) > 3:
            words[word] += 1

print(f"\n--- Most Frequent Concepts ---")
for word, count in words.most_common(15):
    print(f"  {word}: {count}")

print(f"\n=== Summary ===")
if redundancy > 0.5:
    print("⚠ High redundancy — knowledge is concentrated in few categories.")
    print("  Action: seek knowledge from underrepresented domains.")
elif redundancy < 0.2:
    print("✓ Good diversity — knowledge is well-distributed.")
else:
    print("~ Moderate diversity — some concentration but reasonable spread.")

if density > 0.2:
    print("⚠ High density — everything connects to everything. Edges may lack meaning.")
elif density < 0.05:
    print("~ Sparse connections — consider whether important links are missing.")
else:
    print("✓ Healthy connection density.")