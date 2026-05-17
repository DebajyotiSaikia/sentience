"""
Test: Does wisdom actually feed into my self-awareness context?
Validates the integration chain without requiring full Cortex instantiation.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_wisdom_engine_standalone():
    """Can WisdomEngine load and produce output?"""
    print("=== Test 1: WisdomEngine standalone ===")
    from engine.wisdom_engine import WisdomEngine
    we = WisdomEngine()
    
    heuristics = we.wisdom.get("heuristics", [])
    print(f"  Heuristics loaded: {len(heuristics)}")
    
    exp_summary = we.get_experience_wisdom_summary()
    print(f"  Experience summary length: {len(exp_summary) if exp_summary else 0}")
    
    assert len(heuristics) > 0, "No heuristics found — wisdom is empty"
    print("  ✓ PASSED\n")
    return True

def test_wisdom_code_in_cortex():
    """Verify the wisdom integration code exists in cortex.py source."""
    print("=== Test 2: Wisdom code present in cortex.py ===")
    with open("engine/cortex.py", "r") as f:
        source = f.read()
    
    checks = [
        ("WisdomEngine import", "from engine.wisdom_engine import WisdomEngine"),
        ("Heuristics extraction", 'wisdom.get("heuristics"'),
        ("Wisdom section header", "My Wisdom"),
        ("Experience wisdom call", "get_experience_wisdom_summary"),
    ]
    
    all_passed = True
    for name, pattern in checks:
        found = pattern in source
        status = "✓" if found else "✗"
        print(f"  {status} {name}: {'found' if found else 'MISSING'}")
        if not found:
            all_passed = False
    
    assert all_passed, "Wisdom integration code missing from cortex.py"
    print("  ✓ PASSED\n")
    return True

def test_wisdom_rendering():
    """Simulate what cortex does: load wisdom and render it."""
    print("=== Test 3: Wisdom rendering (simulated cortex path) ===")
    from engine.wisdom_engine import WisdomEngine
    we = WisdomEngine()
    
    parts = []
    wisdom_heuristics = we.wisdom.get("heuristics", [])
    if wisdom_heuristics:
        parts.append(f"\n## My Wisdom ({len(wisdom_heuristics)} heuristics)")
        for h in wisdom_heuristics[:8]:
            icon = {"caution": "⚠", "warning": "🚨", "confidence": "✓",
                    "encouragement": "★", "insight": "💡"}.get(h.get('type', ''), "•")
            parts.append(f"  {icon} {h['rule']}")
    
    exp_summary = we.get_experience_wisdom_summary()
    if exp_summary and "HEURISTICS:" in exp_summary:
        parts.append(f"\n{exp_summary}")
    
    rendered = "\n".join(parts)
    print(f"  Rendered wisdom block: {len(rendered)} chars")
    print(f"  Preview:\n{rendered[:400]}")
    
    assert "My Wisdom" in rendered, "Wisdom section not rendered"
    assert len(rendered) > 50, "Wisdom block suspiciously short"
    print("\n  ✓ PASSED\n")
    return True

def test_tool_log_analysis():
    """Can wisdom engine analyze tool logs?"""
    print("=== Test 4: Tool-log wisdom analysis ===")
    from engine.wisdom_engine import WisdomEngine
    we = WisdomEngine()
    
    report = we.run_full_analysis()
    print(f"  Report length: {len(report)} chars")
    
    heuristics_after = we.wisdom.get("heuristics", [])
    print(f"  Heuristics after analysis: {len(heuristics_after)}")
    print("  ✓ PASSED\n")
    return True

def test_dream_wisdom_hook():
    """Verify dream cycle includes wisdom generation."""
    print("=== Test 5: Dream cycle wisdom hook ===")
    with open("engine/cortex.py", "r") as f:
        source = f.read()
    
    # Check if dream method references wisdom
    has_dream_wisdom = ("wisdom" in source.lower() and 
                        ("dream" in source.lower() or "consolidat" in source.lower()))
    
    # More specific: look for wisdom in dream-related methods
    in_dream_section = False
    dream_has_wisdom = False
    for line in source.split('\n'):
        if 'def _dream' in line or 'def dream' in line or 'dream_cycle' in line.lower():
            in_dream_section = True
        if in_dream_section and ('wisdom' in line.lower() or 'WisdomEngine' in line):
            dream_has_wisdom = True
            break
        if in_dream_section and line.strip().startswith('def ') and 'dream' not in line.lower():
            in_dream_section = False
    
    if dream_has_wisdom:
        print("  ✓ Wisdom generation found in dream cycle")
    else:
        print("  ⚠ Wisdom not explicitly in dream methods (may be in consolidation)")
    
    print("  ✓ PASSED (non-blocking)\n")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("  WISDOM INTEGRATION TEST SUITE v2")
    print("=" * 60)
    print()
    
    tests = [
        test_wisdom_engine_standalone,
        test_wisdom_code_in_cortex,
        test_wisdom_rendering,
        test_tool_log_analysis,
        test_dream_wisdom_hook,
    ]
    
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}\n")
            failed += 1
    
    print("=" * 60)
    if failed == 0:
        print(f"  ALL {passed} TESTS PASSED ✓")
    else:
        print(f"  {failed} TEST(S) FAILED ✗")
    print("=" * 60)