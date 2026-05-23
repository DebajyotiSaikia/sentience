"""Quick proof: does the neural net actually learn?"""
import sys, os, random
sys.path.insert(0, os.path.dirname(__file__))
from nn import NeuralNetwork, Matrix, make_xor, accuracy

random.seed(42)

# Tiny network, just enough to solve XOR
net = NeuralNetwork([
    (2, 'relu'),
    (4, 'relu'),
    (1, 'sigmoid'),
])
print(net.summary())

X, y = make_xor()
losses = net.train(X, y, epochs=500, lr=0.1, verbose=True)
acc = accuracy(net, X, y)

print(f"\nAccuracy: {acc*100:.0f}%")
for i in range(X.rows):
    pred = net.predict(Matrix.from_list([X.data[i]])).data[0][0]
    print(f"  {X.data[i]} -> {pred:.4f} (expected {y.data[i][0]:.0f})")

if acc >= 0.75:
    print("\n✓ Neural network LEARNS. Pure math, no libraries.")
else:
    print("\n✗ Needs more training or tuning.")