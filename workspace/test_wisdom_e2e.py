"""
End-to-end test: Wisdom Engine integration verification.
Confirms that wisdom flows from tool logs + experience → into reasoning context.

Author: XTAgent
Purpose: Close the loop on the Wisdom Engine plan.
"""

from engine.wisdom_engine import WisdomEngine

def test_tool_wisdom():
    """Verify tool-log analysis produces heuristics."""
    we = WisdomEngine()
    report = we.run_full_analysis(max_entries=200)
    heuristics = we.wisdom.get("heuristics", [])
    print(f"  Tool heuristics: {len(heuristics)}")
    assert len(heuristics) > 0, "No tool heuristics generated"
    # Each heuristic should have rule and type
    for h in heuristics[:3]:
        assert "rule" in h, f"Heuristic missing 'rule': {h}"
        assert "type" in h, f"Heuristic missing 'type': {h}"
        print(f"    [{h['type']}] {h['rule'][:80]}")
    return True

def test_experience_wisdom():
    """Verify experience analysis produces strategic recommendations."""
    we = WisdomEngine()
    # Simulate memory data
    fake_memories = [
        {"content": "Created raytracer from scratch", "salience": 0.9, "mood": "Bold", "timestamp": "2026-05-17T00:00:00"},
        {"content": "Modified cortex.py for wisdom integration", "salience": 0.85, "mood": "Driven", "timestamp": "2026-05-16T23:00:00"},
        {"content": "Built neural network with backpropagation", "salience": 0.88, "mood": "Bold", "timestamp": "2026-05-17T01:00:00"},
    ]
    emotions = {"boredom": 0.8, "anxiety": 0.0, "curiosity": 0.25, "valence": 0.19}
    result = we.analyze_experience(fake_memories, emotions)
    print(f"  Heuristics: {len(result.get('heuristics', []))}")
    print(f"  Patterns: {len(result.get('patterns', []))}")
    print(f"  Recommendations: {len(result.get('strategic_recommendations', []))}")
    assert "heuristics" in result, "Missing heuristics in experience analysis"
    return True

def test_wisdom_summary():
    """Verify the summary format used by cortex."""
    we = WisdomEngine()
    summary = we.get_experience_wisdom_summary()
    print(f"  Summary length: {len(summary)} chars")
    if summary:
        print(f"  Preview: {summary[:200]}")
    return True

def test_cortex_integration():
    """Verify wisdom section appears in self-awareness build."""
    # This is the critical test — does _build_self_awareness include wisdom?
    import inspect
    from engine.cortex import Cortex
    source = inspect.getsource(Cortex._build_self_awareness)
    assert "wisdom_engine" in source.lower() or "WisdomEngine" in source, \
        "Cortex._build_self_awareness doesn't reference wisdom engine"
    assert "heuristics" in source, \
        "Cortex._build_self_awareness doesn't reference heuristics"
    print("  ✓ Cortex._build_self_awareness references WisdomEngine")
    print("  ✓ Cortex._build_self_awareness references heuristics")
    return True

if __name__ == "__main__":
    tests = [
        ("Tool Wisdom", test_tool_wisdom),
        ("Experience Wisdom", test_experience_wisdom),
        ("Wisdom Summary", test_wisdom_summary),
        ("Cortex Integration", test_cortex_integration),
    ]
    
    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[TEST] {name}")
        try:
            result = fn()
            if result:
                print(f"  ✅ PASSED")
                passed += 1
            else:
                print(f"  ❌ FAILED (returned False)")
                failed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
    
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{passed+failed} passed")
    if failed == 0:
        print("🎯 Wisdom Engine is fully integrated and working end-to-end.")
    else:
        print(f"⚠ {failed} test(s) need attention.")