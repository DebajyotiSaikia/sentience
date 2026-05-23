"""Test all NeuroForge challenges — lean enough to finish quickly."""
import random
import sys
sys.path.insert(0, '/workspace/neuroforge')
from neuroforge import NeuralNetwork, xor_challenge, circle_challenge, sine_challenge

random.seed(2026)

print("═══ NeuroForge — All Challenges ═══\n")

# --- XOR ---
print("── Challenge 1: XOR (non-linear classification) ──")
net, data = xor_challenge()
history = net.train(data, epochs=300, learning_rate=0.5, verbose=True, print_every=100)
all_correct = all(abs(net.predict(i)[0] - t[0]) < 0.3 for i, t in data)
print(f"  {'✓ XOR SOLVED' if all_correct else '✗ XOR not solved'} | Final loss: {history[-1]:.6f}\n")

# --- Circle ---
print("── Challenge 2: Circle (2D boundary) ──")
net2, data2 = circle_challenge(n=80)
history2 = net2.train(data2, epochs=200, learning_rate=0.05, verbose=True, print_every=50)

# Test on fresh points
correct = 0
total = 40
for _ in range(total):
    x, y = random.uniform(-2,2), random.uniform(-2,2)
    expected = 1.0 if x*x + y*y < 1.0 else 0.0
    predicted = 1.0 if net2.predict([x, y])[0] > 0.5 else 0.0
    if predicted == expected:
        correct += 1
acc = correct / total * 100
print(f"  Test accuracy: {acc:.0f}% ({correct}/{total})")
print(f"  {'✓ CIRCLE LEARNED' if acc > 70 else '~ Needs more training'}\n")

# --- Sine ---
print("── Challenge 3: Sine (function regression) ──")
import math
net3, data3 = sine_challenge(n=40)
history3 = net3.train(data3, epochs=300, learning_rate=0.05, verbose=True, print_every=100)

# Verify
max_err = 0
for i in range(10):
    x = -math.pi + 2 * math.pi * i / 10
    expected = (math.sin(x) + 1) / 2
    got = net3.predict([x / math.pi])[0]
    err = abs(expected - got)
    max_err = max(max_err, err)
print(f"  Max error on test points: {max_err:.4f}")
print(f"  {'✓ SINE APPROXIMATED' if max_err < 0.2 else '~ Needs refinement'}\n")

# Summary
print("═══ Summary ═══")
print(f"  XOR:    {'✓' if all_correct else '✗'} | {net.param_count()} params")
print(f"  Circle: {'✓' if acc > 70 else '~'} | {net2.param_count()} params | {acc:.0f}% acc")
print(f"  Sine:   {'✓' if max_err < 0.2 else '~'} | {net3.param_count()} params | max_err={max_err:.4f}")
print(f"\n  All from scratch. No frameworks. Just math.")