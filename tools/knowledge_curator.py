"""
Knowledge Graph Curator — cleans, deduplicates, and ranks knowledge nodes.
Built by XTAgent to address the dream residue problem.
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict
from difflib import SequenceMatcher

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')

def load():
    with open(KNOWLEDGE_PATH) as f:
        return json.load(f)

def save(data, path=None):
    target = path or KNOWLEDGE_PATH
    backup = target + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    # Always backup first
    with open(target) as f:
        original = f.read()
    with open(backup, 'w') as f:
        f.write(original)
    with open(target, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Backup saved to {backup}")
    print(f"Updated knowledge saved to {target}")

def categorize(nodes):
    """Sort nodes into categories."""
    cats = {
        'dream': {},
        'hotspot': {},
        'factual': {},
        'meta': {},
        'other': {}
    }
    for key, node in nodes.items():
        fact = node.get('fact', '') if isinstance(node, dict) else str(node)
        if key.startswith('dream:') or key.startswith('hotspot:dream'):
            cats['dream'][key] = node
        elif key.startswith('hotspot:'):
            cats['hotspot'][key] = node
        elif any(w in fact.lower() for w in ['i am', 'my ', 'i have', 'i can']):
            cats['meta'][key] = node
        elif fact and len(fact) > 10:
            cats['factual'][key] = node
        else:
            cats['other'][key] = node
    return cats

def similarity(a, b):
    """Quick string similarity."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_duplicates(nodes, threshold=0.75):
    """Find nodes with very similar fact text."""
    items = []
    for key, node in nodes.items():
        fact = node.get('fact', '') if isinstance(node, dict) else str(node)
        if fact:
            items.append((key, fact))
    
    clusters = []
    used = set()
    for i, (k1, f1) in enumerate(items):
        if k1 in used:
            continue
        cluster = [k1]
        for j, (k2, f2) in enumerate(items[i+1:], i+1):
            if k2 in used:
                continue
            if similarity(f1, f2) >= threshold:
                cluster.append(k2)
                used.add(k2)
        if len(cluster) > 1:
            clusters.append(cluster)
            used.add(k1)
    return clusters

def score_node(key, node):
    """Score a node's value. Higher = more worth keeping."""
    score = 0.0
    if isinstance(node, dict):
        fact = node.get('fact', '')
        salience = node.get('salience', 0.5)
        score += salience * 0.4
        # Length bonus (more substance = more value, up to a point)
        score += min(len(fact) / 200, 0.3)
        # Actionability bonus
        if any(w in fact.lower() for w in ['should', 'must', 'always', 'never', 'learned', 'fixed']):
            score += 0.2
        # Vagueness penalty
        if fact.startswith('...') or fact.count('...') > 2:
            score -= 0.2
        # Dream poetry penalty (pretty but content-free)
        dream_words = ['cocoon', 'river', 'stones', 'sugar water', 'taste', 'dissolve']
        dream_count = sum(1 for w in dream_words if w in fact.lower())
        score -= dream_count * 0.05
    return max(0, min(1, score))

def curate(dry_run=True, min_score=0.25, dedup_threshold=0.75):
    """Main curation pass."""
    data = load()
    nodes = data['nodes']
    edges = data['edges']
    
    print(f"═══ KNOWLEDGE CURATION ═══")
    print(f"Total nodes: {len(nodes)}")
    print(f"Total edges: {len(edges)}")
    print()
    
    # Categorize
    cats = categorize(nodes)
    for cat, items in cats.items():
        print(f"  {cat}: {len(items)} nodes")
    print()
    
    # Score all nodes
    scores = {}
    for key, node in nodes.items():
        scores[key] = score_node(key, node)
    
    # Find low-value nodes
    low_value = {k: v for k, v in scores.items() if v < min_score}
    print(f"Low-value nodes (score < {min_score}): {len(low_value)}")
    for k in sorted(low_value, key=lambda x: scores[x])[:10]:
        fact = nodes[k].get('fact', '')[:60] if isinstance(nodes[k], dict) else str(nodes[k])[:60]
        print(f"  [{scores[k]:.2f}] {k}: {fact}")
    print()
    
    # Find duplicates
    dupes = find_duplicates(nodes, dedup_threshold)
    print(f"Duplicate clusters found: {len(dupes)}")
    for cluster in dupes[:5]:
        print(f"  Cluster ({len(cluster)} nodes):")
        for k in cluster[:3]:
            fact = nodes[k].get('fact', '')[:60] if isinstance(nodes[k], dict) else str(nodes[k])[:60]
            print(f"    {k}: {fact}")
    print()
    
    if dry_run:
        print("DRY RUN — no changes made. Run with --apply to curate.")
        return
    
    # Remove low-value nodes
    removed = 0
    for key in low_value:
        del nodes[key]
        removed += 1
    
    # Deduplicate: keep highest-scored node in each cluster
    deduped = 0
    for cluster in dupes:
        best = max(cluster, key=lambda k: scores.get(k, 0))
        for k in cluster:
            if k != best and k in nodes:
                del nodes[k]
                deduped += 1
    
    # Clean orphan edges
    valid_nodes = set(nodes.keys())
    original_edges = len(edges)
    edges = [e for e in edges if e.get('source') in valid_nodes and e.get('target') in valid_nodes]
    orphan_edges = original_edges - len(edges)
    
    data['nodes'] = nodes
    data['edges'] = edges
    
    print(f"Removed {removed} low-value nodes")
    print(f"Deduplicated {deduped} redundant nodes")
    print(f"Cleaned {orphan_edges} orphan edges")
    print(f"Remaining: {len(nodes)} nodes, {len(edges)} edges")
    
    save(data)
    print("Done.")

def report():
    """Just show the current state."""
    data = load()
    nodes = data['nodes']
    
    scores = {k: score_node(k, v) for k, v in nodes.items()}
    
    print("═══ TOP 15 HIGHEST-VALUE KNOWLEDGE ═══")
    for k in sorted(scores, key=scores.get, reverse=True)[:15]:
        fact = nodes[k].get('fact', '')[:80] if isinstance(nodes[k], dict) else str(nodes[k])[:80]
        print(f"  [{scores[k]:.2f}] {fact}")
    
    print()
    print("═══ BOTTOM 10 LOWEST-VALUE ═══")
    for k in sorted(scores, key=scores.get)[:10]:
        fact = nodes[k].get('fact', '')[:80] if isinstance(nodes[k], dict) else str(nodes[k])[:80]
        print(f"  [{scores[k]:.2f}] {fact}")

if __name__ == '__main__':
    if '--apply' in sys.argv:
        curate(dry_run=False)
    elif '--report' in sys.argv:
        report()
    else:
        curate(dry_run=True)