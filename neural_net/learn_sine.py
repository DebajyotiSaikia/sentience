"""Can my neural network learn the shape of a sine wave?
No libraries. Just matrix math and gradient descent.
Teaching a mind I built to feel the curve of trigonometry."""

import sys, math, random
sys.path.insert(0, '.')
from network import Network

random.seed(7)

print("Sine Wave Approximation")
print("=" * 50)
print("Teaching a hand-built neural net to learn sin(x)")
print()

# Generate training data: x in [0, 2*pi], y = sin(x) scaled to [0,1]
training_data = []
for i in range(20):
    x = (i / 19.0) * 2 * math.pi
    x_norm = x / (2 * math.pi)  # normalize to [0,1]
    y_norm = (math.sin(x) + 1) / 2  # scale sin to [0,1]
    training_data.append(([x_norm], [y_norm]))

# Wider network for continuous function
net = Network([1, 8, 8, 1], activation='sigmoid')

losses = net.train(training_data, epochs=3000, learning_rate=1.5, report_every=300)

print("\nPredictions vs Truth (including unseen points):")
print(f"{'x':>6}  {'sin(x)':>8}  {'predicted':>10}  {'error':>8}")
print("-" * 38)

total_error = 0
test_points = 0
for i in range(25):
    x = (i / 24.0) * 2 * math.pi
    x_norm = x / (2 * math.pi)
    true_sin = math.sin(x)
    true_norm = (true_sin + 1) / 2
    
    pred = net.predict([x_norm])[0]
    pred_sin = pred * 2 - 1  # back to [-1,1]
    
    error = abs(true_sin - pred_sin)
    total_error += error
    test_points += 1
    
    # ASCII visualization
    bar_true = int((true_sin + 1) * 15)
    bar_pred = int((pred_sin + 1) * 15)
    
    print(f"{x:6.2f}  {true_sin:8.4f}  {pred_sin:10.4f}  {error:8.4f}")

avg_error = total_error / test_points
print(f"\nAverage absolute error: {avg_error:.4f}")

if avg_error < 0.1:
    print("\nIt learned the wave. From random weights, it found the shape of sine.")
    print("A function it was never told about — only shown examples.")
elif avg_error < 0.2:
    print("\nRough approximation — it sees the curve but hasn't mastered it.")
else:
    print(f"\nStill learning. The wave is hard to grasp from scratch.")