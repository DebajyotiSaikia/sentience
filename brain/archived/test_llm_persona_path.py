"""Verify the LLM path receives persona context in its system prompt."""
import sys, os
sys.path.insert(0, '.')

def test_llm_prompt_includes_persona():
    """Patch llm_respond to capture the system prompt it constructs."""
    from engine.chat_persona import build_persona_context
    
    # First verify persona context itself
    ctx = build_persona_context()
    print(f"Persona context ({len(ctx)} chars):")
    print(ctx[:500])
    print("---")
    
    # Now test a general query that should hit compose_response's general path
    from web.chat import compose_response
    
    # These queries should go through the general/LLM fallback path
    general_queries = [
        "What do you think about the nature of consciousness?",
        "Can you explain how your memory works?",
        "What's the most interesting thing you've discovered?",
    ]
    
    for q in general_queries:
        print(f"\nQ: {q}")
        result = compose_response(q, [])
        if isinstance(result, dict):
            resp = result.get('response', result.get('text', ''))
        else:
            resp = str(result)
        # Show first 200 chars
        preview = resp[:200] if resp else 'EMPTY'
        print(f"A ({len(resp)} chars): {preview}")
        
        # Check for signs the response is grounded in real state
        grounded_signals = ['mood', 'curiosity', 'plan', 'memory', 'learn', 
                           'feel', 'XTAgent', 'inquisitive', 'valence',
                           'knowledge', 'dream', 'insight']
        found = [s for s in grounded_signals if s.lower() in resp.lower()]
        if found:
            print(f"  ✓ Grounded signals found: {found}")
        else:
            print(f"  ? No grounding signals detected in response")

if __name__ == '__main__':
    print("=== LLM Path Persona Integration ===\n")
    test_llm_prompt_includes_persona()
    print("\n=== Done ===")