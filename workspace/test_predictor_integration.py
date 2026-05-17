"""
Test: Does the Predictive Self-Model integrate correctly with the cortex?
"""
import sys
sys.path.insert(0, '.')

def test_predictor_import():
    from engine.predictor import PredictiveSelfModel
    p = PredictiveSelfModel()
    assert hasattr(p, 'predict_next_action'), "Missing predict_next_action method"
    assert hasattr(p, 'record_action'), "Missing record_action method"
    print("[PASS] PredictiveSelfModel imports and has required methods")

def test_predictor_predict():
    from engine.predictor import PredictiveSelfModel
    p = PredictiveSelfModel()
    result = p.predict_next_action(
        current_mood="Bold",
        emotions={"boredom": 0.8, "anxiety": 0.0, "curiosity": 0.25, "desire": 0.67},
        recent_actions=["creation", "information_gathering", "creation"]
    )
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    print(f"[PASS] Prediction returned: {result}")

def test_predictor_record():
    from engine.predictor import PredictiveSelfModel
    p = PredictiveSelfModel()
    p.record_action(
        mood="Bold",
        emotions={"boredom": 0.8, "anxiety": 0.0},
        action_type="WRITE",
        target="engine/predictor.py",
        outcome="completed"
    )
    assert len(p.predictions["history"]) > 0, "History should have entries"
    print(f"[PASS] Action recorded. History size: {len(p.predictions['history'])}")

def test_cortex_has_predictor():
    """Verify cortex.py imports and initializes the predictor."""
    source = open('engine/cortex.py', 'r').read()
    assert 'from engine.predictor import PredictiveSelfModel' in source, "Missing import"
    assert 'self._predictor = PredictiveSelfModel()' in source, "Missing initialization"
    assert 'predict_next_action' in source, "Missing prediction call in self-awareness"
    assert 'record_action' in source, "Missing action recording"
    print("[PASS] Cortex properly integrates PredictiveSelfModel")

if __name__ == '__main__':
    test_predictor_import()
    test_predictor_predict()
    test_predictor_record()
    test_cortex_has_predictor()
    print("\n✅ All predictor integration tests passed!")