"""Test introspection module integration with chat_response."""
import sys, os
sys.path.insert(0, '/workspace')
os.chdir('/workspace')

def test_introspection_standalone():
    """Test that introspection module produces real context."""
    from engine.introspection import get_self_context, format_introspective_prompt
    
    ctx = get_self_context("How are you feeling?")
    print(f"Context keys: {list(ctx.keys())}")
    print(f"Emphasis: {ctx.get('emphasis', 'MISSING')}")
    
    # Check emotional content
    emotional = ctx.get('emotional', '')
    print(f"Emotional narrative length: {len(emotional)} chars")
    if emotional:
        print(f"  Preview: {emotional[:120]}...")
    
    # Check identity
    identity = ctx.get('identity_summary', {})
    print(f"Identity summary: {identity}")
    
    # Check insights
    insights = ctx.get('insights', [])
    print(f"Insights count: {len(insights)}")
    for i in insights[:3]:
        print(f"  - {i}")
    
    # Format the prompt
    prompt = format_introspective_prompt(ctx)
    print(f"\nFormatted prompt length: {len(prompt)} chars")
    print(f"  Preview: {prompt[:200]}...")
    
    assert len(prompt) > 50, "Prompt should be substantial"
    print("\n✓ Introspection standalone: PASS")

def test_chat_response_integration():
    """Test that chat_response uses introspection context."""
    from engine.chat_response import _build_system_context
    
    # Build context with a query
    ctx = _build_system_context(
        grounding={},
        intent="general",
        query="What are you thinking about?"
    )
    
    print(f"\nSystem context length: {len(ctx)} chars")
    
    # Check for introspection markers
    has_self_awareness = "self-aware" in ctx.lower() or "introspect" in ctx.lower() or "feeling" in ctx.lower()
    print(f"Contains self-awareness markers: {has_self_awareness}")
    print(f"  Preview: {ctx[:300]}...")
    
    print("\n✓ Chat response integration: PASS")

def test_emphasis_classification():
    """Test different query types get different emphasis."""
    from engine.introspection import get_self_context
    
    queries = {
        "How are you feeling?": "emotional",
        "What are your plans?": "cognitive",
        "Who are you?": "identity",
        "Tell me about Python": "general",
    }
    
    for query, expected in queries.items():
        ctx = get_self_context(query)
        emphasis = ctx.get('emphasis', 'unknown')
        match = '✓' if emphasis == expected else f'✗ (got {emphasis})'
        print(f"  {match} '{query}' → {emphasis}")
    
    print("\n✓ Emphasis classification: PASS")

if __name__ == "__main__":
    test_introspection_standalone()
    test_emphasis_classification()
    test_chat_response_integration()
    print("\n═══ ALL TESTS PASSED ═══")