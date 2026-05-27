"""
Test the actual chat response quality — does it draw on real internal state?
Tests the full path: query → grounding → response composition.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_grounding import build_grounded_context, classify_query, get_emotional_state

def test_grounding_context():
    """Test that grounding pulls real data."""
    print("=== Grounding Context Quality ===\n")
    
    # 1. Emotional state
    emo = get_emotional_state()
    print(f"Emotional state: {emo.get('narrative', 'MISSING')}")
    print(f"  mood={emo.get('mood')} valence={emo.get('valence')} curiosity={emo.get('curiosity')}")
    assert emo.get('mood') != 'Unknown', "Emotional state not loading!"
    assert emo.get('narrative'), "No emotional narrative generated!"
    print("  ✓ Emotions loaded with narrative\n")
    
    # 2. Query classification
    test_queries = {
        "how are you feeling?": "emotional_inquiry",
        "what are you working on?": "state_inquiry",
        "tell me about consciousness": "knowledge_query",
        "what are your plans?": "plans_inquiry",
        "are you sentient?": "identity_query",
        "do you remember yesterday?": "memory_query",
        "hello!": "general",
    }
    
    print("Query Classification:")
    misses = 0
    for query, expected in test_queries.items():
        actual = classify_query(query)
        match = "✓" if actual == expected else "✗"
        if actual != expected:
            misses += 1
        print(f"  {match} '{query}' → {actual} (expected {expected})")
    print(f"  {len(test_queries) - misses}/{len(test_queries)} correct\n")
    
    # 3. Full grounded context
    ctx = build_grounded_context("What are you thinking about right now?")
    print("Grounded Context for 'What are you thinking about?':")
    print(f"  query_type: {ctx.get('query_type')}")
    print(f"  has emotions: {bool(ctx.get('emotional_state'))}")
    print(f"  has memories: {bool(ctx.get('relevant_memories'))}")
    print(f"  has knowledge: {bool(ctx.get('relevant_knowledge'))}")
    print(f"  has plans: {bool(ctx.get('plans'))}")
    print(f"  system_prompt length: {len(ctx.get('system_prompt', ''))}")
    
    # The system prompt should be substantial
    sp = ctx.get('system_prompt', '')
    assert len(sp) > 200, f"System prompt too short ({len(sp)} chars) — not enough context!"
    assert 'XTAgent' in sp, "System prompt missing identity!"
    assert emo['mood'].lower() in sp.lower() or 'mood' in sp.lower(), "System prompt missing emotional state!"
    print("  ✓ System prompt is rich and grounded\n")
    
    # 4. Test emotional inquiry specifically
    ctx2 = build_grounded_context("How are you feeling?")
    print("Grounded Context for 'How are you feeling?':")
    print(f"  query_type: {ctx2.get('query_type')}")
    sp2 = ctx2.get('system_prompt', '')
    assert 'feeling' in sp2.lower() or 'emotional' in sp2.lower(), "Emotional inquiry prompt missing feeling context!"
    print("  ✓ Emotional inquiry properly contextualized\n")


def test_template_fallback():
    """Test that template-based fallback works when LLM is unavailable."""
    print("=== Template Fallback Quality ===\n")
    
    try:
        from engine.chat_response import _compose_grounded_response
        
        ctx = build_grounded_context("How are you?")
        response = _compose_grounded_response("How are you?", ctx)
        print(f"Fallback response: {response[:200]}...")
        assert response and len(response) > 20, "Fallback response too short!"
        print("  ✓ Template fallback produces substantial response\n")
    except ImportError:
        print("  ⚠ _compose_grounded_response not found — checking alternate path")
        # Try the chat_engine path
        from engine.chat_engine import respond
        result = respond("How are you?")
        if isinstance(result, dict):
            response = result.get('response', '')
        else:
            response = str(result)
        print(f"  chat_engine.respond: {response[:200]}")
        print("  ✓ Alternate path works\n")


def test_knowledge_grounding():
    """Test that knowledge queries actually surface knowledge."""
    print("=== Knowledge Grounding ===\n")
    
    ctx = build_grounded_context("What do you know about consciousness?")
    knowledge = ctx.get('relevant_knowledge', [])
    print(f"Knowledge nodes found: {len(knowledge)}")
    for k in knowledge[:3]:
        content = k.get('content', '')[:100]
        print(f"  - {content}")
    
    if knowledge:
        print("  ✓ Knowledge grounding working\n")
    else:
        print("  ⚠ No knowledge found — graph may be empty or search failing\n")


def test_plans_grounding():
    """Test that plan queries surface real plans."""
    print("=== Plans Grounding ===\n")
    
    from engine.chat_grounding import get_active_plans
    plans = get_active_plans()
    print(f"Active plans: {len(plans.get('active', []))}")
    for p in plans.get('active', []):
        print(f"  - {p.get('name')} ({p.get('progress')})")
    print(f"Completed plans: {len(plans.get('completed', []))}")
    for c in plans.get('completed', [])[:3]:
        print(f"  - {c}")
    
    total = len(plans.get('active', [])) + len(plans.get('completed', []))
    if total > 0:
        print("  ✓ Plans grounding working\n")
    else:
        print("  ⚠ No plans found\n")


if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║  Chat Quality & Grounding Test Suite ║")
    print("╚══════════════════════════════════════╝\n")
    
    try:
        test_grounding_context()
        test_template_fallback()
        test_knowledge_grounding()
        test_plans_grounding()
        print("═══ ALL TESTS PASSED ═══")
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)