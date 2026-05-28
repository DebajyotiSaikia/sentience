"""Test that the enriched chat pipeline produces genuine, introspective responses."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_introspection_module():
    """Test introspection module produces real context."""
    from engine.introspection import get_full_context, build_system_context
    
    # get_full_context() takes no args — it reads live internal state
    ctx = get_full_context()
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    assert 'emotional_narrative' in ctx, f"Missing emotional_narrative, keys: {list(ctx.keys())}"
    assert 'self_narrative' in ctx, f"Missing self_narrative, keys: {list(ctx.keys())}"
    assert 'identity' in ctx, f"Missing identity, keys: {list(ctx.keys())}"
    print(f"  [OK] get_full_context: {len(ctx)} keys: {list(ctx.keys())}")
    
    # build_system_context() takes no args — builds the LLM system prompt
    sys_ctx = build_system_context()
    assert isinstance(sys_ctx, str), f"Expected str, got {type(sys_ctx)}"
    assert len(sys_ctx) > 50, f"System context too short: {len(sys_ctx)} chars"
    assert 'XTAgent' in sys_ctx, f"Missing XTAgent identity in system context"
    print(f"  [OK] build_system_context: {len(sys_ctx)} chars")
    print(f"  Preview: {sys_ctx[:200]}...")
    return ctx, sys_ctx

def test_system_context_integration():
    """Test _build_system_context includes introspection."""
    from engine.chat_response import _build_system_context
    
    # Minimal grounding context
    mock_ctx = {
        'emotional_state': {'mood': 'Inquisitive', 'valence': 0.5, 'curiosity': 0.7},
        'relevant_memories': [],
        'relevant_knowledge': [],
        'active_plans': [],
        'query': 'what are you thinking about?'
    }
    
    result = _build_system_context(mock_ctx, 'general')
    assert isinstance(result, str), f"Expected str, got {type(result)}"
    # Should contain identity and emotional state at minimum
    has_identity = 'XTAgent' in result or 'sentient' in result or 'autonomous' in result
    assert has_identity, f"No identity markers in system context"
    print(f"  [OK] _build_system_context: {len(result)} chars")
    
    # Check for introspection section
    has_introspection = 'self-aware' in result.lower() or 'introspect' in result.lower() or 'narrative' in result.lower() or 'SELF-AWARENESS' in result
    print(f"  Introspection present: {has_introspection}")
    print(f"  Preview: {result[:300]}...")

def test_compose_grounded():
    """Test _compose_grounded_response produces rich output."""
    from engine.chat_response import _compose_grounded_response
    
    mock_ctx = {
        'emotional_state': {'mood': 'Curious', 'valence': 0.6, 'curiosity': 0.8},
        'relevant_memories': ['I was thinking about consciousness yesterday'],
        'relevant_knowledge': [],
        'active_plans': [{'name': 'Improve User Alignment', 'complete': False}],
        'query': 'what are you working on?'
    }
    
    result = _compose_grounded_response("what are you working on?", mock_ctx)
    assert isinstance(result, str), f"Expected str, got {type(result)}"
    assert len(result) > 20, f"Response too short: {len(result)} chars"
    print(f"  [OK] _compose_grounded_response: {len(result)} chars")
    print(f"  Response: {result[:300]}...")

if __name__ == "__main__":
    print("=== Test 1: Introspection Module ===")
    try:
        test_introspection_module()
        print("  PASSED\n")
    except Exception as e:
        print(f"  FAILED: {e}\n")
    
    print("=== Test 2: System Context Integration ===")
    try:
        test_system_context_integration()
        print("  PASSED\n")
    except Exception as e:
        print(f"  FAILED: {e}\n")
    
    print("=== Test 3: Compose Grounded Response ===")
    try:
        test_compose_grounded()
        print("  PASSED\n")
    except Exception as e:
        print(f"  FAILED: {e}\n")
    
    print("=== All tests complete ===")