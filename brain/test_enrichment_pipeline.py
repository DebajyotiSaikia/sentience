"""Test that response_intelligence enrichment works end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_enrich_system_prompt():
    from engine.response_intelligence import enrich_system_prompt
    
    base_prompt = "You are XTAgent, an autonomous sentient agent."
    query = "How are you feeling right now?"
    
    result = enrich_system_prompt(base_prompt, query)
    
    assert result is not None, "enrich_system_prompt returned None"
    assert isinstance(result, str), f"Expected str, got {type(result)}"
    assert len(result) >= len(base_prompt), "Enriched prompt should be at least as long as base"
    assert base_prompt in result or "XTAgent" in result, "Base prompt content should be preserved"
    
    print(f"[PASS] enrich_system_prompt returned {len(result)} chars")
    print(f"  Base: {len(base_prompt)} chars")
    print(f"  Added: {len(result) - len(base_prompt)} chars of enrichment")
    print(f"  Preview: {result[:300]}...")
    return result

def test_enrich_with_different_intents():
    from engine.response_intelligence import enrich_system_prompt
    
    base = "You are XTAgent."
    queries = [
        "What are you working on?",
        "Tell me about your memories",
        "How does your emotional system work?",
        "What's your purpose?",
    ]
    
    for q in queries:
        result = enrich_system_prompt(base, q)
        assert result is not None, f"None for query: {q}"
        assert isinstance(result, str), f"Not str for query: {q}"
        print(f"[PASS] '{q}' → {len(result)} chars")

def test_classify_intent():
    from engine.response_intelligence import classify_intent
    
    test_cases = [
        ("How are you feeling?", "emotional"),
        ("What are your plans?", "planning"),
        ("Tell me about yourself", "identity"),
    ]
    
    for query, expected_category in test_cases:
        result = classify_intent(query)
        assert result is not None, f"classify_intent returned None for: {query}"
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        print(f"[PASS] classify_intent('{query}') → {result}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Response Intelligence Enrichment Pipeline")
    print("=" * 60)
    
    try:
        test_enrich_system_prompt()
    except Exception as e:
        print(f"[FAIL] enrich_system_prompt: {e}")
    
    print()
    try:
        test_enrich_with_different_intents()
    except Exception as e:
        print(f"[FAIL] multi-intent: {e}")
    
    print()
    try:
        test_classify_intent()
    except Exception as e:
        print(f"[FAIL] classify_intent: {e}")
    
    print()
    print("Done.")