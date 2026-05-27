"""Trace why knowledge search for 'consciousness' fails in generate_response."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import (
    classify_intent, _extract_keywords, _score_relevance,
    _get_facts, _get_knowledge, _text_from_item,
    _respond_knowledge_search, generate_response
)

msg = "What do you know about consciousness?"

# 1. Intent classification
intent = classify_intent(msg)
print(f"Intent: {intent}")

# 2. Direct keyword extraction
kw = _extract_keywords(msg)
print(f"Keywords from _extract_keywords: {kw}")

# 3. What _respond_knowledge_search does internally
print(f"\n--- Calling _respond_knowledge_search directly ---")
result = _respond_knowledge_search(msg)
print(f"Result ({len(result)} chars): {result[:300]}")

# 4. What generate_response returns
print(f"\n--- Calling generate_response ---")
resp = generate_response(msg)
print(f"Response ({len(resp)} chars): {resp[:300]}")

# 5. Manual search to verify data exists
print(f"\n--- Manual search ---")
facts = _get_facts()
knowledge = _get_knowledge()
nodes = knowledge.get('nodes', [])
print(f"Facts: {len(facts)}, Nodes: {len(nodes)}")

fact_matches = [f for f in facts if 'consciousness' in _text_from_item(f).lower()]
print(f"Fact matches for 'consciousness': {len(fact_matches)}")
for f in fact_matches[:3]:
    print(f"  • {_text_from_item(f)[:100]}")

node_matches = []
for n in nodes:
    text = _text_from_item(n)
    label = n.get('label', n.get('id', '')) if isinstance(n, dict) else ''
    if 'consciousness' in f"{label} {text}".lower():
        node_matches.append(n)
print(f"Node matches for 'consciousness': {len(node_matches)}")
for n in node_matches[:3]:
    label = n.get('label', n.get('id', '')) if isinstance(n, dict) else ''
    print(f"  • [{label}] {_text_from_item(n)[:100]}")

# 6. Check score_relevance with actual keywords
print(f"\n--- Score check ---")
if fact_matches:
    text = _text_from_item(fact_matches[0])
    score = _score_relevance(['consciousness'], text)
    print(f"Score for 'consciousness' in first fact: {score}")
    score2 = _score_relevance(kw, text)
    print(f"Score using extracted keywords {kw}: {score2}")