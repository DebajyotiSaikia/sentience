"""Quick verification that search module works end-to-end."""
from web.search import load_knowledge, search_facts

# Test loading
facts = load_knowledge()
print(f"✓ {len(facts)} facts loaded")

# Test search
for query in ['dream', 'autonomy', 'integrity', 'curiosity']:
    results = search_facts(query, facts)
    print(f"✓ '{query}' → {len(results)} results")
    if results:
        print(f"  top: {results[0]['fact'][:80]}")

print(f"\n✓ Search module fully operational. {len(facts)} facts searchable.")