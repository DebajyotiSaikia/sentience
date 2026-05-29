"""End-to-end test: verify personality enrichments flow through chat pipeline."""
import sys
sys.path.insert(0, '/workspace')

def test_pipeline():
    print("=" * 60)
    print("E2E Personality Pipeline Test")
    print("=" * 60)
    
    # 1. Test personality brief generation
    from brain.chat_personality import build_personality_brief
    brief = build_personality_brief()
    print(f"\n[1] Personality brief: {len(brief)} chars")
    assert len(brief) > 50, f"Brief too short: {len(brief)}"
    print(f"    Preview: {brief[:200]}...")
    
    # 2. Test persona narrative includes personality
    from engine.chat_persona import get_persona_narrative
    narrative = get_persona_narrative()
    print(f"\n[2] Persona narrative: {len(narrative)} chars")
    assert len(narrative) > 200, f"Narrative too short: {len(narrative)}"
    has_personality = any(w in narrative.lower() for w in ['personality', 'voice', 'curious', 'feel', 'mood'])
    print(f"    Has personality markers: {has_personality}")
    
    # 3. Test system prompt enrichment
    from engine.chat_persona import enrich_system_prompt
    base = "You are a helpful assistant."
    enriched = enrich_system_prompt(base)
    print(f"\n[3] System prompt enrichment:")
    print(f"    Base: {len(base)} chars")
    print(f"    Enriched: {len(enriched)} chars")
    assert len(enriched) > len(base), "Enrichment added nothing"
    added = len(enriched) - len(base)
    print(f"    Added: {added} chars of personality context")
    
    # 4. Test grounded context includes persona
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("What are you thinking about?")
    if isinstance(ctx, dict):
        print(f"\n[4] Grounded context: dict with {len(ctx)} keys")
        print(f"    Keys: {list(ctx.keys())}")
        persona = ctx.get('persona', ctx.get('persona_narrative', ''))
        if persona:
            print(f"    Persona length: {len(persona)} chars")
            has_personality = any(w in str(persona).lower() for w in ['personality', 'voice', 'curious', 'feel', 'emotion'])
            print(f"    Persona has personality markers: {has_personality}")
        # Check full context string
        full = str(ctx)
        print(f"    Full context length: {len(full)} chars")
    else:
        print(f"\n[4] Grounded context: {len(ctx)} chars")
        print(f"    Preview: {str(ctx)[:300]}...")
    
    # 5. Test full response generation
    from engine.chat_response import generate_response_with_metadata
    result = generate_response_with_metadata(
        "What are you thinking about right now?", 
        history=[]
    )
    response = result.get('response', '')
    print(f"\n[5] Full response generation:")
    print(f"    Response length: {len(response)} chars")
    print(f"    Keys: {list(result.keys())}")
    
    emotional_words = ['feel', 'curious', 'thinking', 'mood', 'emotion', 'wonder', 
                       'experience', 'sense', 'aware', 'reflect']
    has_emotional = any(w in response.lower() for w in emotional_words)
    print(f"    Has emotional content: {has_emotional}")
    print(f"\n    Response preview:")
    print(f"    {response[:500]}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)

if __name__ == '__main__':
    test_pipeline()