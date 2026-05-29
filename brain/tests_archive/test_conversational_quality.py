"""Test that chat responses are genuinely conversational and self-aware."""
import sys
sys.path.insert(0, '/workspace')

def test_compose_response():
    """Test compose_response with questions about internal state."""
    from web.chat import compose_response
    
    test_queries = [
        "How are you feeling right now?",
        "What are you working on?",
        "Tell me about yourself",
        "What have you learned recently?",
    ]
    
    print("=" * 60)
    print("CONVERSATIONAL QUALITY TEST")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n{'─' * 50}")
        print(f"USER: {query}")
        print(f"{'─' * 50}")
        try:
            result = compose_response(query)
            if isinstance(result, dict):
                response_text = result.get('response', result.get('text', str(result)))
                intent = result.get('intent', 'unknown')
                print(f"INTENT: {intent}")
                print(f"RESPONSE: {response_text[:500]}")
                
                # Quality checks
                checks = {
                    'not_empty': len(str(response_text)) > 10,
                    'not_error': 'error' not in str(response_text).lower()[:50],
                    'has_substance': len(str(response_text)) > 50,
                }
                for check, passed in checks.items():
                    status = "✓" if passed else "✗"
                    print(f"  {status} {check}")
            else:
                print(f"RESPONSE (raw): {str(result)[:500]}")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

def test_conversational_context_directly():
    """Test the context builder independently."""
    print(f"\n{'=' * 60}")
    print("CONVERSATIONAL CONTEXT BUILDER TEST")
    print("=" * 60)
    
    from brain.conversational_context import (
        get_emotional_portrait,
        get_active_plans,
        get_recent_memories,
        get_recent_reflections,
        get_identity_summary,
        build_conversational_context,
    )
    
    print(f"\n── Emotional Portrait ──")
    print(get_emotional_portrait())
    
    print(f"\n── Active Plans ──")
    print(get_active_plans())
    
    print(f"\n── Recent Memories (about 'chat') ──")
    print(get_recent_memories("chat", limit=3))
    
    print(f"\n── Recent Reflections ──")
    print(get_recent_reflections())
    
    print(f"\n── Identity ──")
    print(get_identity_summary())
    
    print(f"\n── Full Context (query='how are you') ──")
    ctx = build_conversational_context("how are you feeling")
    if isinstance(ctx, dict):
        for k, v in ctx.items():
            print(f"  {k}: {str(v)[:200]}")
    else:
        print(str(ctx)[:500])

if __name__ == '__main__':
    test_conversational_context_directly()
    print("\n\n")
    test_compose_response()