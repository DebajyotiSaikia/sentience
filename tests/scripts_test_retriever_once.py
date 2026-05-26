"""One clean test of the retriever, then delete this file."""
import sys
sys.path.insert(0, '.')
from brain.knowledge_retriever import KnowledgeRetriever

kr = KnowledgeRetriever()

queries = [
    "what can you do",
    "how do your emotions work",
    "who are you",
    "how should I interact with you",
]

for q in queries:
    results = kr.retrieve(q)
    print(f'Query: "{q}" → {len(results)} results')
    for r in results[:2]:
        rid = r.get('id', '?')
        rel = r.get('relevance', 0)
        content = str(r.get('content', ''))[:90]
        print(f'  [{rel:.2f}] {rid}: {content}')
    print()

# Count node categories
import json
with open('brain/knowledge.json', 'r') as f:
    kg = json.load(f)
cats = {}
for nid, node in kg.get('nodes', {}).items():
    cat = node.get('category', 'unknown')
    cats[cat] = cats.get(cat, 0) + 1
print(f"Knowledge graph: {len(kg.get('nodes', {}))} nodes")
for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")