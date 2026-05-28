"""Verify knowledge search now handles KG node format (label/content fields)."""
import sys
sys.path.insert(0, '.')

# Test 1: Direct knowledge search with KG-format nodes
print("=== Test 1: knowledge_search handles KG node format ===")
try:
    from engine.knowledge_search import search_knowledge
    # Test with a query that should match knowledge graph content
    results = search_knowledge("emotion", top_k=5)
    print(f"  Results for 'emotion': {len(results)} items")
    for r in results[:3]:
        print(f"    - {r.get('fact', r.get('label', '?'))[:80]}")
    
    results2 = search_knowledge("autonomy", top_k=5)
    print(f"  Results for 'autonomy': {len(results2)} items")
    for r in results2[:3]:
        print(f"    - {r.get('fact', r.get('label', '?'))[:80]}")
except Exception as e:
    print(f"  Error: {e}")

# Test 2: get_relevant_knowledge from grounding
print("\n=== Test 2: chat_grounding.get_relevant_knowledge ===")
try:
    from engine.chat_grounding import get_relevant_knowledge
    results = get_relevant_knowledge("what do you know about yourself", top_k=5)
    print(f"  Results: {len(results)} items")
    for r in results[:5]:
        label = r.get('label', r.get('content', r.get('description', '?')))
        print(f"    - {str(label)[:80]}")
    if results:
        print("  ✓ Knowledge retrieval working!")
    else:
        print("  ✗ No knowledge returned")
except Exception as e:
    print(f"  Error: {e}")

# Test 3: Full grounding context includes knowledge
print("\n=== Test 3: build_grounded_context includes knowledge ===")
try:
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("Tell me about your plans")
    knowledge = ctx.get('relevant_knowledge', [])
    memories = ctx.get('relevant_memories', [])
    print(f"  Knowledge items: {len(knowledge)}")
    print(f"  Memory items: {len(memories)}")
    print(f"  Query type: {ctx.get('query_type', '?')}")
    print(f"  Has emotional state: {bool(ctx.get('emotional_state'))}")
    for k in knowledge[:3]:
        print(f"    knowledge: {str(k.get('content', k.get('label', '?')))[:80]}")
    if knowledge:
        print("  ✓ Knowledge flowing into grounded context!")
    else:
        print("  ⚠ No knowledge in context (may be expected if no matches)")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== Done ===")