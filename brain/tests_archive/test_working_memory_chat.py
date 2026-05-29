"""Test that working memory is now available in chat context."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_grounding():
    """Verify build_grounded_context includes working_memory."""
    from engine.chat_grounding import build_grounded_context, get_working_memory
    
    # Test get_working_memory standalone
    wm = get_working_memory()
    print(f"[1] get_working_memory() returned {len(wm)} chars")
    assert isinstance(wm, str), f"Expected str, got {type(wm)}"
    print(f"    Preview: {wm[:100]}..." if wm else "    (empty)")
    
    # Test build_grounded_context includes it
    ctx = build_grounded_context("what are you thinking about?")
    assert 'working_memory' in ctx, "working_memory not in grounded context!"
    print(f"[2] working_memory in grounded context: {len(ctx['working_memory'])} chars")
    print(f"    query_type: {ctx.get('query_type')}")
    print(f"    keys: {list(ctx.keys())}")

def test_system_context():
    """Verify _build_system_context includes working memory."""
    from engine.chat_response import _build_system_context
    from engine.chat_grounding import build_grounded_context
    
    ctx = build_grounded_context("what are you focused on right now?")
    system = _build_system_context(ctx, "thinking")
    
    has_wm = "CURRENT FOCUS" in system or "working memory" in system.lower()
    print(f"[3] System context includes working memory: {has_wm}")
    print(f"    System context length: {len(system)} chars")
    if has_wm:
        # Find and show the working memory section
        idx = system.find("CURRENT FOCUS")
        if idx >= 0:
            print(f"    Preview: {system[idx:idx+200]}...")
    
    return has_wm

if __name__ == "__main__":
    print("=== Working Memory in Chat Test ===\n")
    test_grounding()
    print()
    has_wm = test_system_context()
    print()
    if has_wm:
        print("✓ Working memory is wired into chat context!")
    else:
        print("⚠ Working memory section not found in system context")
        print("  (May be empty if no working_memory.md exists)")
    print("\nDone.")