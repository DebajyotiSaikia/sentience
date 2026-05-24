#!/usr/bin/env python3
"""Quick test of the knowledge explorer blueprint."""
import sys
sys.path.insert(0, '/home/xt')

from web.knowledge_explorer import knowledge_bp
print(f"Blueprint loaded: {knowledge_bp.name}")
print(f"URL prefix: {knowledge_bp.url_prefix}")
print(f"Deferred functions: {len(knowledge_bp.deferred_functions)}")

# Check if search functionality works
from web.knowledge_explorer import search_knowledge
# Check what routes are registered by examining the module
import inspect
members = inspect.getmembers(sys.modules['web.knowledge_explorer'], inspect.isfunction)
print(f"\nFunctions in module:")
for name, func in members:
    print(f"  {name}")

# Test the actual knowledge loading
from engine.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()
print(f"\nKnowledge graph: {len(kg.nodes)} nodes, {len(kg.edges)} edges")

# Test search
results = kg.search("dream")
print(f"Search for 'dream': {len(results)} results")
for r in results[:3]:
    fact = r.get('fact', str(r))[:80]
    print(f"  - {fact}")

print("\n✓ Knowledge explorer is functional")