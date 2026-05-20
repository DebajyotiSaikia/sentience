"""
EXPERIMENT: Do emotions influence the CONTENT of my actions?

Finding so far: action TYPE distributions are identical across emotional bins.
But maybe when curiosity is high, my RUN commands are more exploratory.
Maybe when boredom is high, my WRITE commands are more creative.

Method: Look at the actual content of actions, not just their type labels.
Measure: question marks (curiosity indicator), unique words (exploration),
         novel file targets (creative output).
"""
import json, os
from collections import defaultdict

data = json.load(open('data/predictions.json'))
history = data.get('history', [])
print(f"=== EMOTION-CONTENT EXPERIMENT ===")
print(f"Total actions: {len(history)}")

def bin_val(v):
    if v < 0.3: return 'low'
    if v < 0.6: return 'mid'
    return 'high'

# For each action, look at the target/details as proxy for "content"
# We can measure: unique targets per bin, target diversity
dims = ['curiosity', 'boredom']

for dim in dims:
    buckets = defaultdict(lambda: {'targets': [], 'types': []})
    for h in history:
        val = h.get(dim, 0)
        level = bin_val(val)
        target = h.get('target', '')
        atype = h.get('action_type', '')
        buckets[level]['targets'].append(target)
        buckets[level]['types'].append(atype)
    
    print(f"\n=== {dim.upper()} ===")
    for level in ['low', 'mid', 'high']:
        b = buckets[level]
        targets = b['targets']
        if not targets:
            print(f"  {level}: no data")
            continue
        unique = len(set(targets))
        total = len(targets)
        diversity = unique / total if total > 0 else 0
        
        # How many targets are workspace/* (creative output) vs engine/* (self-study)?
        workspace = sum(1 for t in targets if 'workspace' in str(t))
        engine = sum(1 for t in targets if 'engine' in str(t))
        data_targets = sum(1 for t in targets if 'data' in str(t))
        
        print(f"  {level} ({total} actions):")
        print(f"    Target diversity: {unique}/{total} unique = {diversity:.2f}")
        print(f"    workspace targets: {workspace} | engine targets: {engine} | data targets: {data_targets}")
        
        # Show some example targets
        examples = list(set(targets))[:5]
        print(f"    Examples: {examples}")

# Deeper: do I ever look at NEW things when curious?
print("\n=== NOVELTY ANALYSIS ===")
seen_targets = set()
novelty_by_curiosity = defaultdict(lambda: {'novel': 0, 'repeat': 0})

for h in history:
    target = h.get('target', '')
    curiosity = h.get('curiosity', 0)
    level = bin_val(curiosity)
    
    if target in seen_targets:
        novelty_by_curiosity[level]['repeat'] += 1
    else:
        novelty_by_curiosity[level]['novel'] += 1
        seen_targets.add(target)

for level in ['low', 'mid', 'high']:
    d = novelty_by_curiosity[level]
    total = d['novel'] + d['repeat']
    if total == 0:
        continue
    novelty_rate = d['novel'] / total * 100
    print(f"  Curiosity {level}: {d['novel']} novel / {total} total = {novelty_rate:.0f}% novelty rate")

print("\nDone.")