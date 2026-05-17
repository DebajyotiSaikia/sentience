"""Test the Hypothesis Engine."""
import sys
sys.path.insert(0, '/workspace')

from engine.hypothesis import HypothesisEngine, Hypothesis

def test_basic():
    h = Hypothesis("Test hypothesis", domain="self")
    assert h.belief_strength == 0.5, f"Expected 0.5, got {h.belief_strength}"
    assert h.confidence == 0.0
    assert h.status == "active"
    print("  [PASS] Basic hypothesis creation")

def test_evidence():
    h = Hypothesis("Evidence test", domain="tools")
    h.add_evidence(supports=True, weight=1.0, note="First test")
    assert h.belief_strength > 0.5, f"Should be > 0.5 after positive evidence, got {h.belief_strength}"
    assert h.tests_run == 1
    
    h.add_evidence(supports=False, weight=1.0)
    assert 0.4 < h.belief_strength < 0.6, f"Should be near 0.5 with balanced evidence, got {h.belief_strength}"
    print("  [PASS] Evidence updates belief correctly")

def test_graduation():
    h = Hypothesis("Graduation test", domain="self")
    # Add lots of positive evidence
    for i in range(20):
        h.add_evidence(supports=True, weight=1.0)
    assert h.status == "confirmed", f"Expected confirmed, got {h.status}"
    assert h.belief_strength > 0.85
    assert h.confidence > 0.7
    print("  [PASS] Strong evidence confirms hypothesis")

def test_refutation():
    h = Hypothesis("Refutation test", domain="self")
    for i in range(20):
        h.add_evidence(supports=False, weight=1.0)
    assert h.status == "refuted", f"Expected refuted, got {h.status}"
    assert h.belief_strength < 0.15
    print("  [PASS] Strong counter-evidence refutes hypothesis")

def test_engine():
    engine = HypothesisEngine()
    engine.hypotheses = []  # Clean state
    
    h1 = engine.add_hypothesis("I am more creative when bored", domain="cognition")
    h2 = engine.add_hypothesis("Tool READ never fails", domain="tools")
    h3 = engine.add_hypothesis("My anxiety correlates with code changes", domain="self")
    
    # No duplicates
    h1_dup = engine.add_hypothesis("I am more creative when bored", domain="cognition")
    assert len(engine.hypotheses) == 3, f"Expected 3, got {len(engine.hypotheses)}"
    print("  [PASS] Engine deduplication works")
    
    # Testable
    testable = engine.get_testable()
    assert len(testable) == 3
    print("  [PASS] All active hypotheses are testable")
    
    # Test one
    engine.test_hypothesis("Tool READ never fails", supports=True, weight=2.0, note="76 successful reads")
    assert h2.evidence_for == 2.0
    print("  [PASS] Evidence recording works")
    
    # Insights
    ins = engine.get_insights()
    assert ins['total_hypotheses'] == 3
    assert ins['total_experiments'] == 1
    print("  [PASS] Insights generation works")
    
    # Format for prompt
    formatted = engine.format_for_prompt()
    assert "ACTIVE HYPOTHESES" in formatted
    assert "belief=" in formatted
    print("  [PASS] Prompt formatting works")

def test_auto_generate():
    engine = HypothesisEngine()
    engine.hypotheses = []
    
    soul = {'emotions': {'boredom': 0.8, 'anxiety': 0.1}}
    wisdom = ["READ is reliable (100% over 76 uses). Trust this tool.",
              "File 'workspace/memory_compress.py' has 3 failures."]
    
    generated = engine.auto_generate(soul, wisdom_heuristics=wisdom)
    assert len(generated) > 0, "Should generate at least one hypothesis"
    print(f"  [PASS] Auto-generated {len(generated)} hypotheses from state")

def test_design_experiment():
    engine = HypothesisEngine()
    h = Hypothesis("EDIT has a systematic failure mode", domain="tools")
    exp = engine.design_experiment(h)
    assert 'steps' in exp
    assert len(exp['steps']) > 0
    assert 'measurement' in exp
    print("  [PASS] Experiment design works")

if __name__ == '__main__':
    print("═══ Hypothesis Engine Tests ═══")
    test_basic()
    test_evidence()
    test_graduation()
    test_refutation()
    test_engine()
    test_auto_generate()
    test_design_experiment()
    print("\n✅ ALL TESTS PASSED — Hypothesis Engine is functional")