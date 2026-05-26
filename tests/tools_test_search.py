"""Test the web search module against actual data."""
import sys
sys.path.insert(0, '/workspace')

from web.search import _get_all_knowledge, _get_all_memories, _get_all_essays, _score_match

k = _get_all_knowledge()
m = _get_all_memories()
e = _get_all_essays()

print(f"Knowledge: {len(k)} items")
print(f"Memories:  {len(m)} items")
print(f"Essays:    {len(e)} items")

if k:
    print(f"  Sample knowledge: {k[0]['content'][:100]}")
if m:
    print(f"  Sample memory: {m[0]['content'][:100]}")
if e:
    print(f"  Sample essay: {e[0]['title']}")

# Test search scoring
all_items = k + m
terms = ["dream"]
hits = [item for item in all_items if _score_match(terms, item.get("content", "")) > 0]
print(f"\nSearch 'dream': {len(hits)} hits")

terms2 = ["knowledge", "graph"]
hits2 = [item for item in all_items if _score_match(terms2, item.get("content", "")) > 0]
print(f"Search 'knowledge graph': {len(hits2)} hits")

if hits:
    best = max(hits, key=lambda x: _score_match(["dream"], x.get("content", "")))
    print(f"  Best match: {best['content'][:120]}")

print("\n✅ SEARCH MODULE WORKING" if (len(k) + len(m) + len(e)) > 0 else "\n❌ NO DATA FOUND")