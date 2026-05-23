#!/usr/bin/env python3
"""Test the KnowledgeCurator - pass a query this time."""
import sys
sys.path.insert(0, '.')

from engine.knowledge_curator import KnowledgeCurator

try:
    kc = KnowledgeCurator()
    print(f"Facts loaded: {len(kc._facts)}")
    print(f"Edges loaded: {len(getattr(kc, '_edges', []))}")
    print(f"Memories loaded: {len(kc._memories)}")
    
    # Test with actual queries
    queries = [
        "What do I know about my own identity?",
        "What have I learned about emotions?",
        "What are my dreams telling me?",
    ]
    
    for q in queries:
        print(f"\n{'='*60}")
        print(f"Query: {q}")
        print(f"{'='*60}")
        result = kc.curate(q)
        if isinstance(result, dict):
            for k, v in result.items():
                print(f"  {k}: {str(v)[:200]}")
        elif isinstance(result, list):
            for item in result[:5]:
                print(f"  - {str(item)[:200]}")
        else:
            print(f"  {str(result)[:500]}")
    
    print("\n=== SUCCESS ===")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\n=== FAILED: {e} ===")