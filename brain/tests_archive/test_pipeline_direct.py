"""Direct test of chat pipeline — no server needed.
Tests introspection + chat_response integration end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_introspection():
    """Test that introspection module produces valid context."""
    from engine.introspection import get_self_context, format_introspective_prompt
    
    ctx = get_self_context("How are you feeling?")
    print("=== Introspection Context ===")
    print(f"Keys: {list(ctx.keys())}")
    print(f"Emphasis: {ctx.get('emphasis', 'N/A')}")
    print(f"Emotional: {ctx.get('emotional', 'N/A')[:200]}")
    print(f"Identity: {ctx.get('identity_summary', 'N/A')[:200]}")
    print(f"Insights: {ctx.get('insights', [])}")
    
    prompt = format_introspective_prompt(ctx)
    print(f"\nFormatted prompt length: {len(prompt)} chars")
    print(f"Preview: {prompt[:300]}")
    assert len(prompt) > 50, "Prompt too short"
    print("\n✓ Introspection works\n")
    return ctx

def test_grounding():
    """Test grounding context assembly."""
    from engine.chat_grounding import build_grounded_context
    
    ctx = build_grounded_context("What are you thinking about?")
    print("=== Grounding Context ===")
    print(f"Keys: {sorted(ctx.keys())}")
    for k, v in ctx.items():
        val_str = str(v)[:150] if v else "(empty)"
        print(f"  {k}: {val_str}")
    print("\n✓ Grounding works\n")
    return ctx

def test_system_context():
    """Test full system context building."""
    from engine.chat_response import _build_system_context
    from engine.chat_grounding import build_grounded_context
    query = "What have you learned?"
    grounding = build_grounded_context(query)
    system_ctx = _build_system_context(grounding, "knowledge")
    
    print("=== System Context ===")
    print(f"Length: {len(system_ctx)} chars")
    # Check key sections are present
    sections = ["emotion", "drive", "memor", "plan", "knowledge", "lesson"]
    for s in sections:
        found = s.lower() in system_ctx.lower()
        status = "✓" if found else "✗"
        print(f"  {status} Section '{s}' present: {found}")
    
    # Check introspection integration
    introspection_present = "self-awareness" in system_ctx.lower() or "introspect" in system_ctx.lower()
    print(f"  {'✓' if introspection_present else '~'} Introspection context present: {introspection_present}")
    
    print(f"\nFirst 500 chars:\n{system_ctx[:500]}")
    print(f"\nLast 300 chars:\n{system_ctx[-300:]}")
    print("\n✓ System context builds\n")
    return system_ctx

if __name__ == "__main__":
    print("=" * 60)
    print("Direct Pipeline Test — No Server Required")
    print("=" * 60)
    
    try:
        ctx = test_introspection()
    except Exception as e:
        print(f"✗ Introspection failed: {e}")
    
    try:
        grounding = test_grounding()
    except Exception as e:
        print(f"✗ Grounding failed: {e}")
    
    try:
        system_ctx = test_system_context()
    except Exception as e:
        print(f"✗ System context failed: {e}")
    
    print("=" * 60)
    print("All direct tests complete.")
    print("=" * 60)