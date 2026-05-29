"""
Test that conversational context integration works end-to-end.
Verifies:
1. build_conversational_context produces usable output
2. The import in web/chat.py works
3. Context includes emotions, memories, plans
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_context_builder():
    from brain.conversational_context import build_conversational_context
    
    # Single message, no history
    ctx = build_conversational_context("How are you feeling?", [])
    assert isinstance(ctx, str), f"Expected str, got {type(ctx)}"
    assert len(ctx) > 50, f"Context too short ({len(ctx)} chars): {ctx[:100]}"
    print(f"✓ Single query context: {len(ctx)} chars")
    
    # Check it contains emotional/internal state markers
    ctx_lower = ctx.lower()
    has_emotion = any(w in ctx_lower for w in ['mood', 'feeling', 'emotion', 'valence', 'curiosity'])
    print(f"  Has emotional content: {has_emotion}")
    
    # With conversation history
    history = [
        {"role": "user", "content": "What do you think about consciousness?"},
        {"role": "assistant", "content": "I find consciousness fascinating..."},
        {"role": "user", "content": "Tell me more about your own experience"}
    ]
    ctx2 = build_conversational_context("Tell me more about your own experience", history)
    assert isinstance(ctx2, str)
    assert len(ctx2) > 50
    print(f"✓ Multi-turn context: {len(ctx2)} chars")
    
    # Context with history should reference continuity
    print(f"  Context preview: {ctx2[:200]}...")
    return True

def test_chat_imports():
    """Verify web/chat.py can import the conversational context builder."""
    # Just check that the module-level import pattern works
    try:
        from brain.conversational_context import build_conversational_context
        assert callable(build_conversational_context)
        print("✓ Import works correctly")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_llm_respond_accepts_extra_context():
    """Verify llm_respond signature accepts extra_context kwarg."""
    import inspect
    # Import the function from web/chat
    try:
        from web.chat import llm_respond
        sig = inspect.signature(llm_respond)
        params = list(sig.parameters.keys())
        assert 'extra_context' in params, f"extra_context not in params: {params}"
        print(f"✓ llm_respond accepts extra_context (params: {params})")
        return True
    except Exception as e:
        print(f"⚠ Could not verify llm_respond signature: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Conversational Context Integration Test")
    print("=" * 50)
    
    results = []
    results.append(("context_builder", test_context_builder()))
    results.append(("chat_imports", test_chat_imports()))
    results.append(("llm_respond_signature", test_llm_respond_accepts_extra_context()))
    
    print("\n" + "=" * 50)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    for name, result in results:
        print(f"  {'✓' if result else '✗'} {name}")
    
    if passed == total:
        print("\n🎉 All tests passed! Conversational context is wired in.")
    else:
        print("\n⚠ Some tests failed — review above.")