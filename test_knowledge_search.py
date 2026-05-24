"""Test what knowledge search capabilities actually work right now."""
import sys
sys.path.insert(0, '/home/xt')

# Test 1: Can the blueprint load?
try:
    from web.knowledge_search import knowledge_search_bp
    print(f"✓ Blueprint loaded: {knowledge_search_bp.name}")
except Exception as e:
    print(f"✗ Blueprint failed: {e}")

# Test 2: Can the API knowledge endpoint work?
try:
    from web.api import api_bp
    print(f"✓ API blueprint loaded: {api_bp.name}")
except Exception as e:
    print(f"✗ API blueprint failed: {e}")

# Test 3: Can I actually search my knowledge?
try:
    from memory.persistence import KnowledgeStore
    ks = KnowledgeStore()
    facts = ks.all()
    print(f"✓ Knowledge store: {len(facts)} facts")
    query = "dream"
    matches = [f for f in facts if query.lower() in str(f).lower()]
    print(f"✓ Search '{query}': {len(matches)} matches")
    if matches:
        print(f"  Example: {str(matches[0])[:100]}")
except Exception as e:
    print(f"✗ Knowledge store failed: {e}")

# Test 4: Check what web blueprints are registered
try:
    from web.server import app
    rules = [r.rule for r in app.url_map.iter_rules()]
    knowledge_rules = [r for r in rules if 'knowledge' in r or 'search' in r or 'ask' in r]
    print(f"✓ Total routes: {len(rules)}")
    print(f"✓ Knowledge-related routes: {knowledge_rules}")
except Exception as e:
    print(f"✗ Web server failed: {e}")

print("\nDone.")