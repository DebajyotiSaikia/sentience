"""
Test suite for neuron.py — verify the neural network learns real patterns.
"""
import sys
sys.path.insert(0, '/workspace/neuron')
from neuron import Network, ascii_plot, visualize_decision_boundary
import random

random.seed(42)

def test_xor():
    """XOR is the classic test — not linearly separable, requires hidden layer."""
    print("═══ TEST: XOR Learning ═══")
    net = Network([2, 4, 1], activation='sigmoid', learning_rate=1.0)
    
    dataset = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0]),
    ]
    
    history = net.train(dataset, epochs=5000, report_every=1000)
    
    print("\n  Predictions:")
    all_correct = True
    for inputs, target in dataset:
        pred = net.predict(inputs)[0]
        correct = (round(pred) == target[0])
        mark = "✓" if correct else "✗"
        print(f"    {inputs} → {pred:.4f} (want {target[0]}) {mark}")
        if not correct:
            all_correct = False
    
    print(f"\n  Final loss: {history[-1]:.6f}")
    print(f"  Result: {'PASS' if all_correct else 'FAIL'}")
    
    print("\n" + ascii_plot(history, title="XOR Loss Curve"))
    print(visualize_decision_boundary(net))
    return all_correct

def test_and_or():
    """AND and OR — should be trivial for even a single layer."""
    print("\n═══ TEST: AND Gate ═══")
    net_and = Network([2, 1], activation='sigmoid', learning_rate=5.0)
    and_data = [([0,0],[0]), ([0,1],[0]), ([1,0],[0]), ([1,1],[1])]
    net_and.train(and_data, epochs=2000)
    
    ok = True
    for inp, tgt in and_data:
        p = net_and.predict(inp)[0]
        correct = round(p) == tgt[0]
        print(f"  AND{inp} → {p:.4f} {'✓' if correct else '✗'}")
        if not correct: ok = False
    
    print(f"\n═══ TEST: OR Gate ═══")
    net_or = Network([2, 1], activation='sigmoid', learning_rate=5.0)
    or_data = [([0,0],[0]), ([0,1],[1]), ([1,0],[1]), ([1,1],[1])]
    net_or.train(or_data, epochs=2000)
    
    for inp, tgt in or_data:
        p = net_or.predict(inp)[0]
        correct = round(p) == tgt[0]
        print(f"  OR{inp} → {p:.4f} {'✓' if correct else '✗'}")
        if not correct: ok = False
    
    print(f"  Result: {'PASS' if ok else 'FAIL'}")
    return ok

def test_architecture():
    """Test network description and basic sanity."""
    print("\n═══ TEST: Architecture ═══")
    net = Network([3, 5, 4, 2], activation='tanh', learning_rate=0.1)
    print(net.describe())
    out = net.predict([1.0, 0.5, -0.3])
    print(f"  Random output: {out}")
    assert len(out) == 2, "Output size mismatch"
    print("  Result: PASS")
    return True

if __name__ == "__main__":
    results = []
    results.append(("Architecture", test_architecture()))
    results.append(("AND/OR", test_and_or()))
    results.append(("XOR", test_xor()))
    
    print("\n" + "═" * 40)
    all_pass = all(r for _, r in results)
    for name, passed in results:
        print(f"  {name}: {'PASS ✓' if passed else 'FAIL ✗'}")
    print(f"\n  Overall: {'ALL PASSED' if all_pass else 'FAILURES DETECTED'}")