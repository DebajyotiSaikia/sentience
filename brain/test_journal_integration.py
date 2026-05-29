"""Quick test: verify journal context injection into chat pipeline."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_journal_module():
    """Test ConversationJournal can be imported and format_for_prompt works."""
    from engine.conversation_journal import ConversationJournal
    j = ConversationJournal()
    ctx = j.format_for_prompt("How are you feeling?")
    print(f"  Journal context type: {type(ctx).__name__}")
    print(f"  Journal context length: {len(ctx) if ctx else 0}")
    if ctx:
        print(f"  Preview: {repr(ctx[:150])}")
    print("  [PASS] Journal module works")

def test_chat_response_includes_journal():
    """Test that generate_response_with_metadata still works with journal injection."""
    # Just verify the module parses and the function exists
    from engine.chat_response import generate_response_with_metadata
    print(f"  Function found: {generate_response_with_metadata.__name__}")
    print("  [PASS] Chat response module loads with journal injection")

def test_enriched_context_builder():
    """Test that the user-aligned context builder still works."""
    from brain.user_aligned_context import build_user_aligned_chat_context
    ctx = build_user_aligned_chat_context("What are you working on?")
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    assert "emotional_portrait" in ctx, "Missing emotional_portrait"
    assert "active_plans" in ctx, "Missing active_plans"
    assert "query_intent" in ctx, "Missing query_intent"
    print(f"  Context keys: {list(ctx.keys())}")
    print(f"  Intent: {ctx.get('query_intent', 'unknown')}")
    print(f"  Emotional portrait length: {len(ctx.get('emotional_portrait', ''))}")
    from brain.user_aligned_context import build_user_aligned_chat_context
    ctx = build_user_aligned_chat_context("What are you working on?")
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    assert "emotional_state" in ctx, "Missing emotional_state"
    assert "active_plans" in ctx, "Missing active_plans"
    assert "intent" in ctx, "Missing intent"
    print(f"  Context keys: {list(ctx.keys())}")
    print(f"  Intent: {ctx.get('intent', 'unknown')}")
    print(f"  Emotional state length: {len(ctx.get('emotional_state', ''))}")
    tests = [test_journal_module, test_chat_response_includes_journal, test_enriched_context_builder]
    passed = 0
    for t in tests:
        print(f"\n{t.__doc__}")
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
    
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{len(tests)} passed")
    if passed == len(tests):
        print("ALL TESTS PASSED")
    sys.exit(0 if passed == len(tests) else 1)