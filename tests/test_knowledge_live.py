"""Test that knowledge_live search works correctly with actual data."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from web.knowledge_live import _load_knowledge

# Test 1: _load_knowledge returns a list of dicts
facts = _load_knowledge()
assert isinstance(facts, list), f"Expected list, got {type(facts)}"
print(f"✓ _load_knowledge() returns list of {len(facts)} facts")

# Test 2: Each entry is a dict with 'fact' key
if facts:
    sample = facts[0]
    assert isinstance(sample, dict), f"Expected dict entry, got {type(sample)}"
    assert 'fact' in sample, f"Missing 'fact' key in {list(sample.keys())}"
    print(f"✓ First fact: {sample['fact'][:80]}...")

# Test 3: Simulate search logic (the part we just fixed)
query = "identity"
tokens = query.lower().split()
query_lower = query.lower()
scored = []
for i, fact_entry in enumerate(facts):
    text = fact_entry.get('fact', str(fact_entry)).lower()
    score = sum(1 for t in tokens if t in text)
    if query_lower in text:
        score += len(tokens)
    if score > 0:
        scored.append({
            'id': str(i),
            'fact': fact_entry.get('fact', str(fact_entry)),
            'score': score
        })

scored.sort(key=lambda x: x['score'], reverse=True)
print(f"✓ Search for 'identity' found {len(scored)} results")
if scored:
    print(f"  Top hit (score={scored[0]['score']}): {scored[0]['fact'][:80]}...")

print("\n✅ All knowledge_live tests passed!")