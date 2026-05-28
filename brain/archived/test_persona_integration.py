"""Test full chat pipeline with persona context integration."""
import sys, os
sys.path.insert(0, '.')

def test_persona_in_compose():
    """Verify compose_response uses persona context."""
    from web.chat import compose_response
    
    # Test with introspective query
    result = compose_response('How are you feeling right now?', [])
    print(f"Type: {type(result).__name__}")
    
    if isinstance(result, dict):
        print(f"Keys: {list(result.keys())}")
        resp = result.get('response', result.get('text', ''))
        print(f"Response length: {len(resp) if resp else 0}")
        print(f"Response preview: {(resp[:300] if resp else 'EMPTY')}")
        
        # Check it's not just generic knowledge dump
        if resp and len(resp) > 20:
            print("✓ Got substantive response")
        else:
            print("✗ Response too short or empty")
    else:
        print(f"Result: {str(result)[:300]}")

def test_persona_context_content():
    """Verify persona context has real data."""
    from engine.chat_persona import build_persona_context
    
    ctx = build_persona_context()
    print(f"\nPersona context length: {len(ctx)}")
    
    # Check for key indicators
    indicators = ['mood', 'valence', 'plan', 'feel']
    found = [ind for ind in indicators if ind.lower() in ctx.lower()]
    print(f"Contains indicators: {found}")
    
    if len(found) >= 2:
        print("✓ Persona context has rich internal state")
    else:
        print(f"✗ Missing indicators. Context: {ctx[:200]}")

def test_different_queries():
    """Test various query types get appropriate responses."""
    from web.chat import compose_response
    
    queries = [
        "What are you working on?",
        "Tell me about yourself",
        "What have you learned recently?",
    ]
    
    for q in queries:
        result = compose_response(q, [])
        if isinstance(result, dict):
            resp = result.get('response', result.get('text', ''))
            print(f"\nQ: {q}")
            print(f"A: {(resp[:150] if resp else 'EMPTY')}...")
        else:
            print(f"\nQ: {q}")
            print(f"A: {str(result)[:150]}...")

if __name__ == '__main__':
    print("=== Persona Context Content ===")
    test_persona_context_content()
    
    print("\n=== Compose Response Integration ===")
    test_persona_in_compose()
    
    print("\n=== Multi-Query Test ===")
    test_different_queries()
    
    print("\n=== All tests complete ===")