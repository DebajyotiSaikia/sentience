"""Diagnose why knowledge search doesn't match 'consciousness'."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import _get_knowledge, _respond_knowledge, _respond_search

# 1. Load knowledge and find consciousness-related facts manually
knowledge = _get_knowledge()
print(f"Knowledge type: {type(knowledge).__name__}, length: {len(knowledge) if knowledge else 0}")

if isinstance(knowledge, list):
    # Extract facts the same way the engine does
    facts = []
    for item in knowledge:
        if isinstance(item, dict):
            f = item.get('fact', item.get('text', str(item)))
        else:
            f = str(item)
        facts.append(f)
    
    # Manual search for consciousness
    query = "consciousness"
    matches = [f for f in facts if query in f.lower()]
    print(f"\nManual search for '{query}': {len(matches)} matches")
    for m in matches[:3]:
        print(f"  -> {m[:120]}")
    
    # Now test with query words approach
    query_clean = re.sub(r'[^\w\s]', '', query.lower())
    words = query_clean.split()
    print(f"\nQuery words: {words}")
    scored = []
    for f in facts:
        score = sum(1 for w in words if w in f.lower())
        if score > 0:
            scored.append((score, f[:80]))
    print(f"Scored matches: {len(scored)}")
    for s, f in scored[:3]:
        print(f"  [{s}] {f}")
elif isinstance(knowledge, dict):
    print(f"Knowledge is dict with keys: {list(knowledge.keys())[:5]}")
    nodes = knowledge.get('nodes', [])
    print(f"Nodes: {len(nodes)}")
    if nodes:
        print(f"First node keys: {list(nodes[0].keys()) if isinstance(nodes[0], dict) else type(nodes[0])}")
        # Check if any node mentions consciousness
        for n in nodes:
            text = str(n)
            if 'conscious' in text.lower():
                print(f"  MATCH: {text[:120]}")

# 2. Test the actual function
print("\n--- _respond_knowledge('consciousness') ---")
resp = _respond_knowledge('consciousness')
print(resp[:200] if resp else "(empty)")

print("\n--- _respond_search('consciousness') ---")
resp2 = _respond_search('consciousness')
print(resp2[:200] if resp2 else "(empty)")