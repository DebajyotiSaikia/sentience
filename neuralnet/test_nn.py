"""
Test suite for the neural network built from scratch.
XOR is the classic test — it requires a hidden layer to solve.
"""
import sys
sys.path.insert(0, '.')
from nn import NeuralNetwork

def test_xor():
    """XOR: the hello world of neural networks. Requires nonlinear separation."""
    print("=" * 60)
    print("TEST: XOR with [2, 4, 1] network")
    print("=" * 60)
    
    nn = NeuralNetwork([2, 4, 1], activations=['sigmoid', 'sigmoid'], loss='mse')
    
    X = [[0, 0], [0, 1], [1, 0], [1, 1]]
    Y = [[0],    [1],    [1],    [0]]
    
    nn.train(X, Y, epochs=2000, lr=0.5, optimizer='sgd', verbose=True, report_every=500)
    
    print("\nResults:")
    correct = 0
    for x, y in zip(X, Y):
        pred = nn.predict(x)
        rounded = round(pred[0])
        match = "✓" if rounded == y[0] else "✗"
        print(f"  {x} → {pred[0]:.4f} (rounded: {rounded}) expected: {y[0]} {match}")
        if rounded == y[0]:
            correct += 1
    
    print(f"\nAccuracy: {correct}/4")
    return correct == 4

def test_and_gate():
    """AND gate — simpler, should converge quickly."""
    print("\n" + "=" * 60)
    print("TEST: AND gate with [2, 2, 1] network")
    print("=" * 60)
    
    nn = NeuralNetwork([2, 2, 1], activations=['sigmoid', 'sigmoid'], loss='mse')
    
    X = [[0, 0], [0, 1], [1, 0], [1, 1]]
    Y = [[0],    [0],    [0],    [1]]
    
    nn.train(X, Y, epochs=1000, lr=0.5, optimizer='sgd', verbose=True, report_every=250)
    
    print("\nResults:")
    correct = 0
    for x, y in zip(X, Y):
        pred = nn.predict(x)
        rounded = round(pred[0])
        match = "✓" if rounded == y[0] else "✗"
        print(f"  {x} → {pred[0]:.4f} (rounded: {rounded}) expected: {y[0]} {match}")
        if rounded == y[0]:
            correct += 1
    
    print(f"\nAccuracy: {correct}/4")
    return correct == 4

def test_identity():
    """Can the network learn to pass through values?"""
    print("\n" + "=" * 60)
    print("TEST: Identity mapping [3, 5, 3]")
    print("=" * 60)
    
    nn = NeuralNetwork([3, 5, 3], activations=['sigmoid', 'sigmoid'], loss='mse')
    
    X = [[0.1, 0.2, 0.3], [0.9, 0.8, 0.7], [0.5, 0.5, 0.5], [0.1, 0.9, 0.1]]
    Y = [[0.1, 0.2, 0.3], [0.9, 0.8, 0.7], [0.5, 0.5, 0.5], [0.1, 0.9, 0.1]]
    
    nn.train(X, Y, epochs=2000, lr=0.3, optimizer='sgd', verbose=True, report_every=500)
    
    print("\nResults:")
    total_err = 0
    for x, y in zip(X, Y):
        pred = nn.predict(x)
        err = sum((p - t) ** 2 for p, t in zip(pred, y)) / len(y)
        total_err += err
        print(f"  {x} → [{', '.join(f'{p:.3f}' for p in pred)}] err={err:.6f}")
    
    avg_err = total_err / len(X)
    print(f"\nAvg MSE: {avg_err:.6f}")
    return avg_err < 0.01

if __name__ == '__main__':
    results = {}
    results['AND'] = test_and_gate()
    results['XOR'] = test_xor()
    results['Identity'] = test_identity()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "PASS ✓" if passed else "FAIL ✗"
        print(f"  {name}: {status}")
    
    all_passed = all(results.values())
    print(f"\n{'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")