"""Quick test of the ask system."""
import sys
sys.path.insert(0, '.')

from web.ask import create_ask_blueprint

bp = create_ask_blueprint()

# Test topic extraction
topics = bp.extract_topics(top_n=10)
print(f"Found {len(topics)} topics:")
for t in topics:
    print(f"  {t}")

# Test search
results = bp.search_knowledge("dream")
print(f"\nSearch for 'dream': {len(results)} results")
for r in results[:3]:
    print(f"  - {r.get('fact', r)[:80]}")

print("\nAsk system: OK")