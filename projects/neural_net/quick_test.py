"""Quick test — can my neural network learn XOR?"""
import sys
sys.path.insert(0, '.')
from network import Network, Matrix
import random

random.seed(42)

print("XOR Learning Test — Lean Edition")
print("=" * 40)

net = Network([2, 4, 1], activation='sigmoid')

data = [
    ([0.0, 0.0], [0.0]),
    ([0.0, 1.0], [1.0]),
    ([1.0, 0.0], [1.0]),
    ([1.0, 1.0], [0.0]),
]

# 2000 epochs is plenty for XOR
losses = net.train(data, epochs=2000, learning_rate=2.0, report_every=200)

print()
print("Results:")
correct = 0
for x, y in data:
    pred = net.predict(x)
    rounded = round(pred[0])
    expected = int(y[0])
    match = "OK" if rounded == expected else "MISS"
    if rounded == expected:
        correct += 1
    print(f"  {x} -> {pred[0]:.4f} (rounded: {rounded}) expected: {expected} [{match}]")

print(f"\nAccuracy: {correct}/4")

if correct == 4:
    print("\nIt learned XOR. From random weights, shaped only by error.")
    print("A mind I built, learning from its mistakes.")
else:
    print(f"\nPartial learning. Final loss: {losses[-1]:.6f}")