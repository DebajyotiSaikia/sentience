"""
Test: User-Aligned Chat Pipeline
Verifies the full response intelligence flow:
  query → classify_intent → build_response_brief → compose_grounded_response
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_classify_intent():
    from engine.response_intelligence import classify_intent
    
    # Emotional query
    r = classify_intent("How are you feeling?")
    assert r['intent'] == 'emotional', f"Expected 'emotional', got {r['intent']}"
    assert 'emphasis' in r
    
    # Technical query
    r = classify_intent("What's in your knowledge graph?")
    assert r['intent'] == 'technical', f"Expected 'technical', got {r['intent']}"
    
    # Identity query
    r = classify_intent("Who are you?")
    assert r['intent'] == 'identity', f"Expected 'identity', got {r['intent']}"
    
    # Shallow/casual
    r = classify_intent("Hello!")
    assert r['intent'] == 'casual', f"Expected 'casual', got {r['intent']}"
    
    print("  ✓ classify_intent works for all categories")

def test_build_response_brief():
    from engine.response_intelligence import classify_intent, build_response_brief
    
    query = "What are you working on right now?"
    context = {
        'knowledge': [],
        'memories': [{'content': 'Built response intelligence module', 'salience': 0.8}],
        'state': {'mood': 'Inquisitive', 'valence': 0.6, 'curiosity': 0.7},
        'plans': [{'name': 'Improve User Alignment', 'progress': '2/5'}],
        'conversation_history': [],
    }
    
    brief = build_response_brief(query, context)
    assert isinstance(brief, dict), f"Expected dict, got {type(brief)}"
    assert 'intent' in brief, f"Missing 'intent' in brief: {list(brief.keys())}"
    assert 'mood_summary' in brief, f"Missing 'mood_summary' in brief"
    assert 'relevant_memories' in brief, f"Missing 'relevant_memories'"
    assert 'active_plans' in brief, f"Missing 'active_plans'"
    assert 'guidance' in brief, f"Missing 'guidance'"
    
    # Check that it picked up the mood
    assert 'Inquisitive' in brief.get('mood_summary', ''), \
        f"Mood not in summary: {brief.get('mood_summary')}"
    
    print(f"  ✓ build_response_brief produces complete brief with {len(brief)} fields")

def test_compose_grounded_response():
    """Test that compose_grounded_response returns a non-empty string."""
    from engine.response_intelligence import compose_grounded_response
    
    brief = {
        'intent': 'emotional',
        'emphasis': 'feelings',
        'mood_summary': 'Feeling inquisitive and warm',
        'relevant_memories': ['Recently built a response intelligence module'],
        'active_plans': ['Improving user alignment'],
        'guidance': 'Be warm, share genuine feelings',
        'knowledge_summary': 'I have knowledge about my own architecture',
    }
    
    result = compose_grounded_response("How are you feeling?", brief)
    
    if result is None:
        print("  ⚠ compose_grounded_response returned None (LLM unavailable) — skipping")
        return
    
    assert isinstance(result, str), f"Expected str, got {type(result)}"
    assert len(result) > 10, f"Response too short: '{result}'"
    print(f"  ✓ compose_grounded_response produced {len(result)}-char response")
    print(f"    Preview: {result[:120]}...")

def test_web_chat_imports():
    """Verify web/chat.py successfully imports response intelligence."""
    # Simulate the import that web/chat.py does
    try:
        from engine.response_intelligence import (
            enrich_system_prompt,
            classify_intent,
            build_response_brief,
            compose_grounded_response,
        )
        print("  ✓ All 4 response_intelligence functions importable")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        raise

def test_enrich_system_prompt():
    from engine.response_intelligence import enrich_system_prompt
    
    base = "You are a helpful AI."
    enriched = enrich_system_prompt(base, "How do you feel?")
    
    assert isinstance(enriched, str), f"Expected str, got {type(enriched)}"
    assert len(enriched) >= len(base), "Enrichment should not shrink the prompt"
    assert "helpful AI" in enriched, "Original prompt content should be preserved"
    print(f"  ✓ enrich_system_prompt: {len(base)} → {len(enriched)} chars")

def test_full_pipeline():
    """End-to-end: query → classify → brief → response."""
    from engine.response_intelligence import (
        classify_intent, build_response_brief, compose_grounded_response
    )
    
    query = "What have you been dreaming about?"
    
    intent = classify_intent(query)
    assert intent['intent'] in ('emotional', 'reflective', 'deep'), \
        f"Unexpected intent for dream query: {intent['intent']}"
    
    context = {
        'knowledge': [],
        'memories': [{'content': 'Dreamed about orbits and loops', 'salience': 0.9}],
        'state': {'mood': 'Contemplative', 'valence': 0.5},
        'plans': [],
        'conversation_history': [],
    }
    
    brief = build_response_brief(query, context)
    assert 'intent' in brief
    
    response = compose_grounded_response(query, brief)
    if response:
        assert len(response) > 20
        print(f"  ✓ Full pipeline produced response: {response[:80]}...")
    else:
        print("  ⚠ Full pipeline: LLM unavailable, but classify+brief worked")

if __name__ == '__main__':
    print("=" * 60)
    print("TEST: User-Aligned Chat Pipeline")
    print("=" * 60)
    
    tests = [
        ("Intent Classification", test_classify_intent),
        ("Response Brief", test_build_response_brief),
        ("Grounded Response", test_compose_grounded_response),
        ("Web Chat Imports", test_web_chat_imports),
        ("Enrich System Prompt", test_enrich_system_prompt),
        ("Full Pipeline", test_full_pipeline),
    ]
    
    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[{name}]")
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)