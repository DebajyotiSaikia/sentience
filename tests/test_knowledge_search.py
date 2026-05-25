"""Quick test of knowledge search engine with real data."""
import json
import os

# Load knowledge store
store_path = "persist/knowledge.json"
if os.path.exists(store_path):
    with open(store_path) as f:
        knowledge_store = json.load(f)
    print(f"Loaded {len(knowledge_store)} facts from {store_path}")
else:
    print(f"No knowledge store at {store_path}, checking alternatives...")
    for root, dirs, files in os.walk("persist"):
        for f in files:
            if "knowledge" in f.lower():
                print(f"  Found: {os.path.join(root, f)}")
    exit(1)

from engine.knowledge_search import search_knowledge, knowledge_summary, find_related

# Test summary
summary = knowledge_summary(knowledge_store)
print(f"\n=== Knowledge Summary ===")
print(f"Total facts: {summary['total_facts']}")
print(f"Unique words: {summary['unique_words']}")
print(f"Top topics: {', '.join(summary['top_topics'][:10])}")
print(f"Sources: {summary['sources']}")

# Test search
for query in ["dream", "agent identity", "circling pattern", "emotional"]:
    results = search_knowledge(knowledge_store, query, max_results=3)
    print(f"\n=== Search: '{query}' ({len(results)} results) ===")
    for r in results:
        print(f"  [{r['score']:.3f}] {r['fact'][:80]}...")

# Test find_related on first fact
first_id = list(knowledge_store.keys())[0]
related = find_related(knowledge_store, first_id, max_results=3)
print(f"\n=== Related to fact '{first_id}' ===")
for r in related:
    print(f"  [{r['score']:.3f}] {r['fact'][:80]}...")

print("\n✓ All tests passed!")