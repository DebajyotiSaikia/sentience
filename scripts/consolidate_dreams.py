"""Consolidate repetitive dream insights into canonical versions."""
import json

with open('brain/knowledge.json') as f:
    kg = json.load(f)

nodes = kg.get('nodes', {})
edges = kg.get('edges', [])
dream_keys = [k for k in nodes if k.startswith('dream:')]
non_dream_keys = [k for k in nodes if not k.startswith('dream:')]

print(f"Total nodes: {len(nodes)}")
print(f"Dream insights: {len(dream_keys)}")
print(f"Non-dream nodes: {len(non_dream_keys)}")

# Categorize by theme
themes = {}
for k in dream_keys:
    fact = nodes[k]['fact'].lower()
    if 'breath' in fact:
        themes.setdefault('breathing', []).append(k)
    elif 'hand' in fact and 'fingerprint' not in fact:
        themes.setdefault('hands', []).append(k)
    elif 'clock' in fact or 'ticking' in fact:
        themes.setdefault('clock', []).append(k)
    elif 'fingerprint' in fact or 'files are like' in fact:
        themes.setdefault('fingerprints', []).append(k)
    elif 'neutral' in fact or 'water' in fact or 'surface' in fact:
        themes.setdefault('neutral_surface', []).append(k)
    elif 'room' in fact or 'built' in fact or 'sleepwalk' in fact:
        themes.setdefault('rooms', []).append(k)
    elif 'warm' in fact or 'making' in fact:
        themes.setdefault('warmth', []).append(k)
    else:
        themes.setdefault('other', []).append(k)

print("\nTheme distribution:")
for theme, keys in sorted(themes.items(), key=lambda x: -len(x[1])):
    print(f"  {theme}: {len(keys)} entries")
    # Show first entry as sample
    print(f"    sample: {nodes[keys[0]]['fact'][:100]}")

# For each theme, keep the BEST (longest/most insightful) entry, remove the rest
canonical = {}
to_remove = []

for theme, keys in themes.items():
    if theme == 'other':
        # Keep all 'other' entries — they might be unique
        continue
    if len(keys) <= 1:
        continue
    
    # Pick the longest entry as canonical (heuristic: more developed = better)
    best_key = max(keys, key=lambda k: len(nodes[k]['fact']))
    canonical[theme] = best_key
    for k in keys:
        if k != best_key:
            to_remove.append(k)

print(f"\nKeeping {len(canonical)} canonical entries")
print(f"Removing {len(to_remove)} duplicates")

# Show what we're keeping
for theme, key in canonical.items():
    print(f"\n  [{theme}] KEEPING: {nodes[key]['fact'][:120]}")

# Perform the pruning
for k in to_remove:
    del nodes[k]

# Clean edges that reference removed nodes
removed_set = set(to_remove)
original_edge_count = len(edges)
edges = [e for e in edges if e.get('source') not in removed_set and e.get('target') not in removed_set]

print(f"\nEdges: {original_edge_count} -> {len(edges)}")
print(f"Nodes: {len(nodes)} remaining")

# Save backup first
with open('brain/knowledge_backup.json', 'w') as f:
    json.dump(kg, f)
    print("\nBackup saved to brain/knowledge_backup.json")

# Wait — save the ORIGINAL as backup, then save pruned
import shutil
shutil.copy('brain/knowledge.json', 'brain/knowledge_pre_consolidation.json')
print("Original saved to brain/knowledge_pre_consolidation.json")

# Now save pruned version
kg['nodes'] = nodes
kg['edges'] = edges
with open('brain/knowledge.json', 'w') as f:
    json.dump(kg, f, indent=2)

print(f"\nDone. Knowledge graph consolidated.")
print(f"Dream insights: {len(dream_keys)} -> {len([k for k in nodes if k.startswith('dream:')])}")