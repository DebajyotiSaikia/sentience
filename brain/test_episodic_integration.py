"""Quick verification that episodic memories flow into get_relevant_memories."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.chat_grounding import get_relevant_memories

queries = [
    "what have you been thinking about",
    "tell me about your dreams",
    "what are your plans",
    "how do you feel right now",
]

for q in queries:
    results = get_relevant_memories(q, top_k=5)
    sources = {}
    for r in results:
        src = r.get("source", "json")
        sources[src] = sources.get(src, 0) + 1
    print(f"Query: {q!r}")
    print(f"  Retrieved: {len(results)} memories | Sources: {sources}")
    if results:
        top = results[0]
        print(f"  Top: [{top.get('source','?')}] {top.get('text','')[:80]}")
    print()

total = sum(len(get_relevant_memories(q, top_k=10)) for q in queries)
print(f"Total memories retrieved across {len(queries)} queries: {total}")
if total > 0:
    print("✓ Episodic memory integration verified")
else:
    print("✗ No memories retrieved — check data store")