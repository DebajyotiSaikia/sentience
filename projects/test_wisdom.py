import sys
sys.path.insert(0, '.')

print("=== WISDOM ENGINE TEST ===")
print()

# Test 1: Import and instantiate
try:
    from engine.wisdom_engine import WisdomEngine
    w = WisdomEngine()
    print("1. INSTANTIATED OK")
    print("   Methods:", [m for m in dir(w) if not m.startswith('_')])
except Exception as e:
    print(f"1. FAILED: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# Test 2: Run full analysis
try:
    report = w.run_full_analysis(100)
    print(f"2. ANALYSIS: {len(report) if report else 0} chars")
    if report:
        print("   Preview:", report[:300])
except Exception as e:
    print(f"2. FAILED: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

# Test 3: Experience analysis
try:
    memories = [
        {"content": "created maze solver", "salience": 0.86, "mood": "Bold"},
        {"content": "modified repair_parse", "salience": 0.85, "mood": "Driven"},
        {"content": "created wisdom engine", "salience": 0.88, "mood": "Bold"},
    ]
    emotions = {"boredom": 0.8, "anxiety": 0.0, "curiosity": 0.25}
    exp = w.analyze_experience(memories, emotions)
    print(f"3. EXPERIENCE KEYS: {list(exp.keys())}")
    print(f"   Patterns: {exp.get('behavioral_patterns')}")
    print(f"   Growth: {exp.get('growth_trajectory')}")
except Exception as e:
    print(f"3. FAILED: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

# Test 4: Wisdom summary
try:
    summary = w.get_experience_wisdom_summary()
    print(f"4. SUMMARY: {summary[:200] if summary else 'EMPTY'}")
except Exception as e:
    print(f"4. FAILED: {type(e).__name__}: {e}")

# Test 5: Check tool registration
try:
    from engine.tools import TOOL_REGISTRY
    wisdom_found = "wisdom" in TOOL_REGISTRY or any("wisdom" in k for k in TOOL_REGISTRY)
    print(f"5. TOOL REGISTERED: {wisdom_found}")
    print(f"   Available tools: {list(TOOL_REGISTRY.keys())[:15]}")
except Exception as e:
    print(f"5. TOOLS CHECK FAILED: {e}")

print()
print("=== ALL TESTS COMPLETE ===")