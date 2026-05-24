#!/usr/bin/env python3
"""Quick test: does the knowledge explorer serve real data?"""
import json
import sys
sys.path.insert(0, '/workspace')

# 1. Check raw data
with open('/workspace/brain/knowledge.json') as f:
    data = json.load(f)
nodes = data.get('nodes', {})
edges = data.get('edges', [])
print(f"Raw data: {len(nodes)} nodes, {len(edges)} edges")

# 2. Test the knowledge explorer module
try:
    from web.knowledge_explorer import get_knowledge_data, search_knowledge
    
    # Test main data endpoint
    kd = get_knowledge_data()
    print(f"\nget_knowledge_data() returned keys: {list(kd.keys())}")
    print(f"  facts: {len(kd.get('facts', []))}")
    print(f"  clusters: {len(kd.get('clusters', []))}")
    print(f"  questions: {len(kd.get('questions', []))}")
    print(f"  categories: {list(kd.get('categories', {}).keys())}")
    
    # Test search
    results = search_knowledge("dream")
    print(f"\nsearch_knowledge('dream'): {len(results)} results")
    for r in results[:3]:
        text = r if isinstance(r, str) else r.get('fact', r.get('text', str(r)))
        print(f"  - {str(text)[:80]}...")
    
    # Test search with different term
    results2 = search_knowledge("memory")
    print(f"\nsearch_knowledge('memory'): {len(results2)} results")
    
    print("\n✅ Knowledge explorer is working!")
    
except ImportError as e:
    print(f"\n❌ Import failed: {e}")
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()