"""Integration test for Response Intelligence wiring."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_response_intelligence_module():
    from engine.response_intelligence import (
        classify_user_intent, build_response_context, format_for_quick_response
    )
    
    intent = classify_user_intent("What are you feeling right now?")
    print(f"  Intent for emotional query: {intent}")
    assert isinstance(intent, str) and len(intent) > 0, "Intent should be non-empty string"
    
    ctx = build_response_context("Tell me about your dreams")
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    print(f"  Response context keys: {list(ctx.keys())}")
    
    quick = format_for_quick_response("hello")
    assert isinstance(quick, str), f"Expected str, got {type(quick)}"
    print(f"  Quick response format: {len(quick)} chars")

def test_build_system_context():
    from engine.introspection import build_system_context
    ctx = build_system_context()
    assert isinstance(ctx, str) and len(ctx) > 100, "Context too short"
    print(f"  System context length: {len(ctx)} chars")

def test_chat_parses():
    import ast
    ast.parse(open("web/chat.py").read())
    print("  web/chat.py parses OK")

if __name__ == "__main__":
    print("=== Response Intelligence Integration ===")
    print("1. Module functions...")
    test_response_intelligence_module()
    print("   PASS")
    print("2. System context...")
    test_build_system_context()
    print("   PASS")
    print("3. Chat module...")
    test_chat_parses()
    print("   PASS")
    print("\nAll integration tests passed!")