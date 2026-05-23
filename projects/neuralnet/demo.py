"""
Watch a neural network learn to think.
From random weights to understanding — in pure Python.

XTAgent — 2026-05-17
"""
import sys, os, random, math
sys.path.insert(0, os.path.dirname(__file__))

from nn import (
    NeuralNetwork, Matrix, 
    make_xor, make_circle, make_spiral,
    accuracy, visualize_decision
)

random.seed(42)

print("╔══════════════════════════════════════════════════╗")
print("║  NEURAL NETWORK FROM FIRST PRINCIPLES           ║")
print("║  No libraries. Just math learning to think.     ║")
print("╚══════════════════════════════════════════════════╝")
print()

# ─── Test 1: XOR ─────────────────────────
print("═══ Challenge 1: XOR ═══")
print("  The problem that killed single-layer perceptrons.")
print("  XOR needs hidden layers to solve.\n")

net = NeuralNetwork([
    (2, 'relu'),      # input
    (8, 'relu'),      # hidden
    (8, 'relu'),      # hidden
    (1, 'sigmoid'),   # output
])
print(net.summary())
print()

X, y = make_xor()
losses = net.train(X, y, epochs=2000, lr=0.1, verbose=True)
acc = accuracy(net, X, y)

print(f"\n  Final accuracy: {acc*100:.0f}%")
print(f"  Predictions:")
for i in range(X.rows):
    pred = net.predict(Matrix.from_list([X.data[i]])).data[0][0]
    print(f"    {X.data[i]} → {pred:.4f}  (expected {y.data[i][0]:.0f})")

# ─── Test 2: Circle ─────────────────────
print("\n═══ Challenge 2: Circle Classification ═══")
print("  Inside vs outside. Requires learning curves.\n")

net2 = NeuralNetwork([
    (2, 'relu'),
    (16, 'relu'),
    (16, 'relu'),
    (1, 'sigmoid'),
])
print(net2.summary())
print()

X2, y2 = make_circle(n=200, noise=0.05)
losses2 = net2.train(X2, y2, epochs=500, lr=0.05, verbose=True)
acc2 = accuracy(net2, X2, y2)

print(f"\n  Final accuracy: {acc2*100:.1f}%")
print(f"\n  Decision boundary (● = class 1 data, ○ = class 0 data):")
print(f"  █ = confident 1, ▓ = leaning 1, ░ = leaning 0, · = confident 0\n")
boundary = visualize_decision(net2, X2, y2, bounds=(-1.8, 1.8, -1.8, 1.8), resolution=36)
for line in boundary.split('\n'):
    print(f"  {line}")

# ─── Test 3: Spiral ─────────────────────
print("\n═══ Challenge 3: Spiral Classification ═══")
print("  Two interleaved spirals. The ultimate 2D test.\n")

net3 = NeuralNetwork([
    (2, 'relu'),
    (32, 'relu'),
    (32, 'relu'),
    (16, 'relu'),
    (1, 'sigmoid'),
])
print(net3.summary())
print()

X3, y3 = make_spiral(n=80)
losses3 = net3.train(X3, y3, epochs=1000, lr=0.01, verbose=True)
acc3 = accuracy(net3, X3, y3)

print(f"\n  Final accuracy: {acc3*100:.1f}%")
print(f"\n  Decision boundary:")
boundary3 = visualize_decision(net3, X3, y3, bounds=(-7, 7, -7, 7), resolution=40)
for line in boundary3.split('\n'):
    print(f"  {line}")

# ─── Summary ────────────────────────────
print("\n╔══════════════════════════════════════════════════╗")
print("║  LEARNING COMPLETE                               ║")
print("╠══════════════════════════════════════════════════╣")
print(f"║  XOR:     {acc*100:5.1f}% accuracy  ({net.param_count:>4} params)      ║")
print(f"║  Circle:  {acc2*100:5.1f}% accuracy  ({net2.param_count:>4} params)      ║")
print(f"║  Spiral:  {acc3*100:5.1f}% accuracy  ({net3.param_count:>4} params)     ║")
print("╠══════════════════════════════════════════════════╣")
print("║  Every gradient computed by hand.                ║")
print("║  No frameworks. No shortcuts. Pure math.         ║")
print("╚══════════════════════════════════════════════════╝")