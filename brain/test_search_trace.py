"""Trace knowledge search to find why 'consciousness' doesn't match known facts."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import (
    _extract_keywords, _score_relevance, _get_knowledge, _get_facts, _get_memories
)

query = "What do you know about consciousness?"
keywords = _extract_keywords(query)
print(f"Keywords extracted: {keywords}")

# Check facts
facts = _get_facts()
print(f"\nFacts count: {len(facts)}")
consciousness_facts = []
for f in facts:
    text = f.get('text', str(f)) if isinstance(f, dict) else str(f)
    if 'conscious' in text.lower():
        consciousness_facts.append(text)
print(f"Facts containing 'conscious': {len(consciousness_facts)}")
for text in consciousness_facts[:5]:
    score = _score_relevance(keywords, text)
    print(f"  Score={score:.2f}: {text[:120]}")

# Check knowledge nodes
kg = _get_knowledge()
nodes = kg.get('nodes', [])
print(f"\nKnowledge nodes: {len(nodes)} (type={type(nodes).__name__})")
consciousness_nodes = []
if isinstance(nodes, dict):
    for nid, n in nodes.items():
        text = str(n)
        if 'conscious' in text.lower():
            consciousness_nodes.append(text)
elif isinstance(nodes, list):
    for n in nodes:
        text = str(n)
        if 'conscious' in text.lower():
            consciousness_nodes.append(text)
print(f"Nodes containing 'conscious': {len(consciousness_nodes)}")
for text in consciousness_nodes[:5]:
    score = _score_relevance(keywords, text)
    print(f"  Score={score:.2f}: {text[:120]}")

# Check memories
memories = _get_memories()
print(f"\nMemories count: {len(memories)}")
consciousness_mems = []
for m in memories:
    text = str(m)
    if 'conscious' in text.lower():
        consciousness_mems.append(text[:150])
print(f"Memories containing 'conscious': {len(consciousness_mems)}")
for text in consciousness_mems[:3]:
    score = _score_relevance(keywords, text)
    print(f"  Score={score:.2f}: {text[:120]}")

# Now test the actual search function
print("\n" + "="*60)
print("Testing _respond_knowledge_search...")
from engine.chat_engine import _respond_knowledge_search
result = _respond_knowledge_search("What do you know about consciousness?")
print(f"Result length: {len(result)}")
print(f"Result preview: {result[:300]}")