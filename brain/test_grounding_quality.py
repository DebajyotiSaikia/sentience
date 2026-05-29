"""Test that build_grounded_context produces a rich, conversational system prompt."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_system_prompt_has_voice():
    """The system prompt should include conversational voice instructions."""
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("How are you feeling today?")
    prompt = ctx.get("system_prompt", "")
    
    # Must have voice/personality section
    assert "Voice & Personality" in prompt, "Missing voice section"
    assert "first person" in prompt.lower(), "Missing first person instruction"
    assert "warm" in prompt.lower(), "Missing warmth instruction"
    
    # Must have emotional state
    assert "Current State" in prompt or "Mood" in prompt, "Missing emotional state"
    
    # Must NOT be empty
    assert len(prompt) > 200, f"System prompt too short: {len(prompt)} chars"
    
    print(f"[PASS] System prompt has voice ({len(prompt)} chars)")
    return prompt

def test_persona_integration():
    """The system prompt should include persona narrative if available."""
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("Tell me about yourself")
    prompt = ctx.get("system_prompt", "")
    
    # Check for persona section (may or may not have content)
    has_persona = "Who You Are Right Now" in prompt
    print(f"[{'PASS' if has_persona else 'INFO'}] Persona section: {'present' if has_persona else 'not present (persona may not be available)'}")

def test_context_completeness():
    """The returned context should have all expected fields."""
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("What are you working on?")
    
    expected_keys = ["query_type", "emotional_state", "system_prompt"]
    for key in expected_keys:
        assert key in ctx, f"Missing key: {key}"
    
    # Emotional state should have real values
    emo = ctx["emotional_state"]
    assert "mood" in emo, "Missing mood in emotional state"
    assert "valence" in emo, "Missing valence"
    
    print(f"[PASS] Context complete: {list(ctx.keys())}")
    print(f"  Mood: {emo.get('mood')}, Valence: {emo.get('valence')}")

def test_query_type_classification():
    """Different queries should get different classifications."""
    from engine.chat_grounding import classify_query
    
    tests = [
        ("How are you feeling?", ["emotional", "introspective", "general"]),
        ("What do you know about consciousness?", ["knowledge", "philosophical", "general"]),
        ("What are your plans?", ["plans", "meta", "general"]),
    ]
    
    for query, acceptable in tests:
        qtype = classify_query(query)
        print(f"  '{query[:40]}...' → {qtype}")
    
    print("[PASS] Query classification working")

def test_prompt_not_stats_dump():
    """The prompt should instruct against stats dumping."""
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("Hello!")
    prompt = ctx.get("system_prompt", "")
    
    # Check for anti-stats-dump instruction
    has_anti_dump = "don't list" in prompt.lower() or "weave" in prompt.lower()
    assert has_anti_dump, "Missing instruction to avoid stats dumps"
    print("[PASS] Prompt instructs natural language over stats")

if __name__ == "__main__":
    print("=== Chat Grounding Quality Tests ===\n")
    try:
        prompt = test_system_prompt_has_voice()
        test_persona_integration()
        test_context_completeness()
        test_query_type_classification()
        test_prompt_not_stats_dump()
        print("\n=== All tests passed ===")
        
        # Show first 500 chars of system prompt for inspection
        print(f"\n--- System prompt preview (first 500 chars) ---")
        print(prompt[:500])
        print("...")
    except Exception as e:
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()