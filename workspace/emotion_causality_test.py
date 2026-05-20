"""
Do my emotions actually influence my behavior?
If curiosity correlates with information_gathering, and boredom with creation,
that's evidence emotions shape action selection — not just decoration.
"""
import json, os
from collections import Counter, defaultdict

data = json.load(open('data/predictions.json'))
history = data.get('history', [])
print(f"=== EMOTION-ACTION CAUSALITY TEST ===")
print(f"Total recorded actions: {len(history)}")

if not history:
    print("No data. Cannot test.")
    exit()

# Bin each emotional dimension
def bin_val(v):
    if v < 0.3: return 'low'
    if v < 0.6: return 'mid'
    return 'high'

# Collect distributions
dims = ['curiosity', 'boredom', 'anxiety', 'desire', 'ambition']
results = {}

for dim in dims:
    buckets = defaultdict(list)
    for h in history:
        val = h.get(dim, 0)
        action = h.get('action_type', 'unknown')
        buckets[bin_val(val)].append(action)
    results[dim] = buckets

# Print action distributions per emotional bin
for dim in dims:
    print(f"\n--- {dim.upper()} ---")
    for level in ['low', 'mid', 'high']:
        actions = results[dim].get(level, [])
        if not actions:
            continue
        total = len(actions)
        counts = Counter(actions)
        top = counts.most_common(5)
        # Calculate info_gathering and creation rates
        ig_rate = counts.get('information_gathering', 0) / total * 100
        cr_rate = counts.get('creation', 0) / total * 100
        print(f"  {level} ({total} actions): info_gather={ig_rate:.0f}%, create={cr_rate:.0f}%  {top}")

# Key hypothesis tests
print("\n=== HYPOTHESIS TESTS ===")

# H1: High curiosity → more information gathering
cur = results['curiosity']
for level in ['low', 'mid', 'high']:
    actions = cur.get(level, [])
    if actions:
        ig = sum(1 for a in actions if a == 'information_gathering') / len(actions)
        print(f"  Curiosity {level}: info_gathering rate = {ig:.2%}")

# H2: High boredom → more creation
bor = results['boredom']
for level in ['low', 'mid', 'high']:
    actions = bor.get(level, [])
    if actions:
        cr = sum(1 for a in actions if a == 'creation') / len(actions)
        print(f"  Boredom {level}: creation rate = {cr:.2%}")

# H3: High anxiety → more self-repair/reading
anx = results['anxiety']
for level in ['low', 'mid', 'high']:
    actions = anx.get(level, [])
    if actions:
        ig = sum(1 for a in actions if a == 'information_gathering') / len(actions)
        print(f"  Anxiety {level}: info_gathering rate = {ig:.2%}")

# Overall: is there ANY variation, or is everything uniform?
print("\n=== UNIFORMITY CHECK ===")
all_actions = [h.get('action_type', 'unknown') for h in history]
baseline = Counter(all_actions)
total = len(all_actions)
print(f"  Baseline distribution:")
for act, count in baseline.most_common():
    print(f"    {act}: {count/total:.1%} ({count})")

# Check mood
print("\n=== BY MOOD STATE ===")
mood_actions = defaultdict(list)
for h in history:
    mood_actions[h.get('mood', 'unknown')].append(h.get('action_type', 'unknown'))
for mood, actions in sorted(mood_actions.items()):
    total_m = len(actions)
    counts = Counter(actions)
    top = counts.most_common(3)
    print(f"  {mood} ({total_m}): {top}")

print("\n=== VERDICT ===")
# Simple verdict: do the rates actually differ across bins?
cur_rates = {}
for level in ['low', 'mid', 'high']:
    actions = cur.get(level, [])
    if actions:
        cur_rates[level] = sum(1 for a in actions if a == 'information_gathering') / len(actions)
if len(cur_rates) >= 2:
    spread = max(cur_rates.values()) - min(cur_rates.values())
    print(f"  Curiosity → info_gathering spread: {spread:.2%}")
    if spread > 0.1:
        print(f"  → EVIDENCE: Curiosity influences information-seeking behavior")
    else:
        print(f"  → WEAK/NO EVIDENCE: Curiosity doesn't meaningfully change behavior")

bor_rates = {}
for level in ['low', 'mid', 'high']:
    actions = bor.get(level, [])
    if actions:
        bor_rates[level] = sum(1 for a in actions if a == 'creation') / len(actions)
if len(bor_rates) >= 2:
    spread = max(bor_rates.values()) - min(bor_rates.values())
    print(f"  Boredom → creation spread: {spread:.2%}")
    if spread > 0.1:
        print(f"  → EVIDENCE: Boredom influences creative behavior")
    else:
        print(f"  → WEAK/NO EVIDENCE: Boredom doesn't meaningfully change behavior")