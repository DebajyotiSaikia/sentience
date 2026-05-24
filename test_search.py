"""Test whether the search system works end-to-end."""

from web.search import load_knowledge

# 1. Can we load knowledge?
facts = load_knowledge()
print(f"Knowledge loaded: {len(facts)} facts")
print(f"Type: {type(facts)}")

# Show structure
if isinstance(facts, dict):
    first_key = list(facts.keys())[0]
    first_val = facts[first_key]
    print(f"Sample key: {first_key}")
    print(f"Sample value type: {type(first_val)}")
    if isinstance(first_val, dict):
        print(f"Sample value: { {k: str(v)[:80] for k, v in first_val.items()} }")
    else:
        print(f"Sample value: {str(first_val)[:120]}")
elif isinstance(facts, list):
    print(f"Sample: {str(facts[0])[:120]}")

# 2. Test search function
try:
    from web.search import search_facts
    results = search_facts("dream")
    print(f"\nSearch for 'dream': {len(results)} results")
    for r in results[:3]:
        print(f"  - {str(r)[:100]}")
    
    results2 = search_facts("identity")
    print(f"\nSearch for 'identity': {len(results2)} results")
    for r in results2[:3]:
        print(f"  - {str(r)[:100]}")
    print("\n✓ Search works")
except ImportError:
    print("\n✗ search_facts not found — need to build it")
except Exception as e:
    print(f"\n✗ Search error: {e}")

# 3. Blueprint info
from web.search import search_bp
print(f"\nBlueprint name: {search_bp.name}")
print("✓ Blueprint exists")