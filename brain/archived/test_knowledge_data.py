"""Diagnose why knowledge search fails for known topics."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_engine import _extract_keywords, _score_relevance, _get_knowledge, _get_facts, _get_memories, _text_from_item

# Test keyword extraction
for q in ["consciousness", "fractals", "What do you know about consciousness?"]:
    kws = _extract_keywords(q)
    print(f"Keywords for '{q}': {kws}")

print()

# Check knowledge data
knowledge = _get_knowledge()
nodes = knowledge.get('nodes', [])
print(f"Knowledge nodes: {len(nodes)}")
if nodes:
    for n in nodes[:5]:
        text = _text_from_item(n)
        print(f"  Sample: {text[:100]}")
    # Search for consciousness
    for n in nodes:
        text = _text_from_item(n)
        if 'conscious' in text.lower():
            print(f"  MATCH: {text[:150]}")

print()

# Check facts
facts = _get_facts()
print(f"Facts: {len(facts)}")
if facts:
    for f in facts[:3]:
        text = _text_from_item(f)
        print(f"  Sample: {text[:100]}")
    for f in facts:
        text = _text_from_item(f)
        if 'conscious' in text.lower():
            print(f"  FACT MATCH: {text[:150]}")

print()

# Check memories
memories = _get_memories(limit=50)
print(f"Memories: {len(memories)}")
for m in memories[:3]:
    text = _text_from_item(m)
    if 'conscious' in text.lower() or 'fractal' in text.lower():
        print(f"  MEM MATCH: {text[:150]}")

# Now test the actual scoring
print("\n--- Scoring test ---")
test_text = "Integrated Information Theory says consciousness corresponds to integrated information"
kws = _extract_keywords("consciousness")
score = _score_relevance(kws, test_text)
print(f"Score for 'consciousness' vs IIT text: {score} (keywords={kws})")