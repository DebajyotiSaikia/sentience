from web.ask import search_knowledge

results = search_knowledge('curiosity')
print(f'Results: {len(results)}')
for r in results[:3]:
    score = r.get('score', 0)
    text = r.get('text', '')[:80]
    print(f'  [{score:.2f}] {text}')

# Test stemming helps
results2 = search_knowledge('dreaming')
print(f'\n"dreaming" results: {len(results2)}')
for r in results2[:3]:
    score = r.get('score', 0)
    text = r.get('text', '')[:80]
    print(f'  [{score:.2f}] {text}')