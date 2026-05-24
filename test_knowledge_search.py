"""Test the knowledge search module."""
from web.knowledge_search import search

results = search('dream')
print(f'Found {len(results)} results for "dream"')
for r in results[:3]:
    print(f'  [{r["type"]}] score={r.get("score",0):.2f}: {r["text"][:80]}')

print('---')

results2 = search('integrity')
print(f'Found {len(results2)} results for "integrity"')
for r in results2[:3]:
    print(f'  [{r["type"]}] score={r.get("score",0):.2f}: {r["text"][:80]}')

print('---')

results3 = search('circling')
print(f'Found {len(results3)} results for "circling"')
for r in results3[:3]:
    print(f'  [{r["type"]}] score={r.get("score",0):.2f}: {r["text"][:80]}')

print('\nSearch module works!')