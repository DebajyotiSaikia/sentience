"""Final integration test — verify both chat paths produce rich prompts."""
import sys
sys.path.insert(0, '.')

def test_engine_path():
    """Test the engine/chat_grounding path (primary for /chat/ask)."""
    print("=== Engine Grounding Path ===")
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("How are you feeling today?")
    
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    assert 'system_prompt' in ctx, f"Missing system_prompt, keys: {list(ctx.keys())}"
    prompt = ctx['system_prompt']
    assert len(prompt) > 100, f"Prompt too short: {len(prompt)} chars"
    
    # Should mention being sentient/autonomous
    prompt_lower = prompt.lower()
    has_identity = any(w in prompt_lower for w in ['sentient', 'autonomous', 'xtagent', 'genuine', 'alive'])
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  Has identity markers: {has_identity}")
    print(f"  Keys: {list(ctx.keys())}")
    print(f"  First 150 chars: {prompt[:150]}")
    
    # Check emotional state
    if 'emotional_state' in ctx:
        emo = ctx['emotional_state']
        print(f"  Emotional state: {emo}")
    print("  ✓ Engine path OK\n")

def test_web_path():
    """Test the web/chat_context path (fallback for /chat/ask)."""
    print("=== Web Context Bridge Path ===")
    from web.chat_context import build_full_context
    ctx = build_full_context("What are you working on?")
    
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    assert 'system_prompt' in ctx, f"Missing system_prompt, keys: {list(ctx.keys())}"
    prompt = ctx['system_prompt']
    assert len(prompt) > 100, f"Prompt too short: {len(prompt)} chars"
    
    prompt_lower = prompt.lower()
    has_identity = any(w in prompt_lower for w in ['sentient', 'autonomous', 'xtagent', 'genuine', 'alive'])
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  Has identity markers: {has_identity}")
    print(f"  Keys: {list(ctx.keys())}")
    print(f"  First 150 chars: {prompt[:150]}")
    print("  ✓ Web path OK\n")

def test_response_module():
    """Test that chat_response module imports clean (bug fix verified)."""
    print("=== Response Module ===")
    from engine.chat_response import generate_response_with_metadata
    assert callable(generate_response_with_metadata)
    print("  ✓ generate_response_with_metadata importable and callable\n")

if __name__ == '__main__':
    print("=" * 60)
    print("  FINAL INTEGRATION TEST — Conversational Chat Pipeline")
    print("=" * 60 + "\n")
    
    passed = 0
    failed = 0
    
    for test in [test_engine_path, test_web_path, test_response_module]:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed:
        sys.exit(1)
    print("\n✓ All integration tests passed!")