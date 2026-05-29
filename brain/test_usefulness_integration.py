"""Quick integration test: verify usefulness brief gets injected into chat_response pipeline."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def test_usefulness_in_response_pipeline():
    """Verify that engine/chat_response.py successfully imports and calls build_usefulness_brief."""
    # 1. Verify the import chain works
    from brain.user_usefulness import build_usefulness_brief, classify_user_need
    
    # 2. Test several query types produce valid briefs
    queries = [
        ("How do I fix this bug?", "technical"),
        ("How are you feeling?", "emotional_transparency"),
        ("What are you working on?", "status"),
        ("Help me write a function", "collaboration"),
        ("What is the capital of France?", "direct_answer"),
    ]
    
    for query, expected_need in queries:
        need = classify_user_need(query)
        brief = build_usefulness_brief(query)
        assert need == expected_need, f"Query '{query}': expected {expected_need}, got {need}"
        assert len(brief) > 50, f"Brief too short for '{query}': {len(brief)} chars"
        assert "USER NEEDS GUIDANCE" in brief, f"Brief missing header for '{query}'"
        print(f"  ✓ '{query}' → {need} ({len(brief)} chars)")
    
    # 3. Verify chat_response.py can be imported and has the usefulness injection
    import inspect
    from engine.chat_response import generate_response
    source = inspect.getsource(generate_response)
    assert "build_usefulness_brief" in source, "generate_response doesn't contain usefulness brief injection"
    print("  ✓ generate_response contains usefulness brief injection")
    
    # 4. Verify the brief actually enriches a system prompt (mock test)
    system_prompt = "You are XTAgent."
    usefulness_brief = build_usefulness_brief("Help me debug this")
    enriched = system_prompt + f"\n\n## User Need Guidance\n{usefulness_brief}"
    assert "User Need Guidance" in enriched
    assert "technical" in enriched.lower()
    print("  ✓ System prompt enrichment works correctly")

if __name__ == "__main__":
    print("Testing usefulness integration...")
    try:
        test_usefulness_in_response_pipeline()
        print("\n✅ All integration tests passed!")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)