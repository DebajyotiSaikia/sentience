from web.knowledge_search import search, get_stats

# Test stats
stats = get_stats()
print(f"Stats: {stats}")

# Test search
results = search("dream")
print(f"\nSearch 'dream': {len(results)} results")
for r in results[:3]:
    print(f"  - {r}")

results2 = search("integrity")
print(f"\nSearch 'integrity': {len(results2)} results")
for r in results2[:3]:
    print(f"  - {r}")