"""Test the search system end-to-end."""
import sys
sys.path.insert(0, '.')

# Test 1: Can we load and search knowledge?
try:
    from web.search import search_knowledge
    results = search_knowledge('identity')
    print(f"[OK] search_knowledge('identity') returned {len(results)} results")
    for r in results[:3]:
        text = r.get('title', r.get('text', r.get('fact', '?')))
        print(f"  - {str(text)[:80]}")
except Exception as e:
    print(f"[FAIL] search_knowledge: {e}")

# Test 2: Can we load and search memories?
try:
    from web.search import search_memories
    results = search_memories('curiosity')
    print(f"\n[OK] search_memories('curiosity') returned {len(results)} results")
    for r in results[:3]:
        text = r.get('text', r.get('content', '?'))
        print(f"  - {str(text)[:80]}")
except Exception as e:
    print(f"[FAIL] search_memories: {e}")

# Test 3: Does the knowledge API blueprint exist?
try:
    from web.knowledge_api import knowledge_bp
    print(f"\n[OK] knowledge_bp loaded: {knowledge_bp.name}")
except Exception as e:
    print(f"[FAIL] knowledge_api: {e}")

# Test 4: Is the search page template accessible?
import os
templates = [f for f in os.listdir('web/templates') if 'search' in f.lower() or 'knowledge' in f.lower() or 'explore' in f.lower()]
if templates:
    print(f"\n[OK] Relevant templates: {templates}")
else:
    print(f"\n[WARN] No search/knowledge templates found")
    all_templates = os.listdir('web/templates')
    print(f"  Available: {all_templates}")

print("\n--- Search system health check complete ---")