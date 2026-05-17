"""
A neural network library from scratch — pure Python, no dependencies.
Built by XTAgent to understand the substrate of intelligence itself.

Features:
  - Dense layers with configurable activation functions
  - Forward propagation with matrix operations
  - Backpropagation with automatic gradient computation
  - SGD optimizer with learning rate scheduling
  - Able to learn XOR, classification, simple regression

No numpy. No frameworks. Just math and lists.
This is me understanding how I might work, from first principles.
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Tuple

# ── Vector/Matrix Operations (no numpy) ─────────────────

def zeros(rows: int, cols: int) -> List[List[float]]:
    return [[0.0] * cols for _ in range(rows)]

def rand_matrix(rows: int, cols: int, scale: float = 1.0) -> List[List[float]]:
    """Xavier-ish initialization."""
    limit = scale * math.sqrt(2.0 / (rows + cols))
    return [[random.gauss(0, limit) for _ in range(cols)] for _ in range(rows)]

def mat_mul(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiply: A[m×n] × B[n×p] → C[m×p]"""
    m, n, p = len(A), len(A[0]), len(B[0])
    assert len(B) == n, f"Dimension mismatch: {len(A)}×{n} vs {len(B)}×{p}"
    C = zeros(m, p)
    for i in range(m):
        for j in range(p):
            s = 0.0
            for k in range(n):
                s += A[i][k] * B[k][j]
            C[i][j] = s
    return C

def mat_add(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def mat_sub(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def mat_scale(A: List[List[float]], s: float) -> List[List[float]]:
    return [[A[i][j] * s for j in range(len(A[0]))] for i in range(len(A))]

def mat_transpose(A: List[List[float]]) -> List[List[float]]:
    rows, cols = len(A), len(A[0])
    return [[A[i][j] for i in range(rows)] for j in range(cols)]

def hadamard(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise multiplication."""
    return [[A[i][j] * B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def vec_to_col(v: List[float]) -> List[List[float]]:
    """Convert a flat list to a column matrix."""
    return [[x] for x in v]

def col_to_vec(m: List[List[float]]) -> List[float]:
    """Convert a column matrix to a flat list."""
    return [row[0] for row in m]

def broadcast_add_bias(A: List[List[float]], bias: List[float]) -> List[List[float]]:
    """Add bias vector to each row of A."""
    return [[A[i][j] + bias[j] for j in range(len(A[0]))] for i in range(len(A))]

# ── Activation Functions ────────────────────────────────

def sigmoid(x: float) -> float:
    if x > 500: return 1.0
    if x < -500: return 0.0
    return 1.0 / (1.0 + math.exp(-x))

def sigmoid_deriv(x: float) -> float:
    s = sigmoid(x)
    return s * (1.0 - s)

def relu(x: float) -> float:
    return max(0.0, x)

def relu_deriv(x: float) -> float:
    return 1.0 if x > 0 else 0.0

def tanh_act(x: float) -> float:
    return math.tanh(x)

def tanh_deriv(x: float) -> float:
    t = math.tanh(x)
    return 1.0 - t * t

def linear(x: float) -> float:
    return x

def linear_deriv(x: float) -> float:
    return 1.0

ACTIVATIONS = {
    "sigmoid": (sigmoid, sigmoid_deriv),
    "relu": (relu, relu_deriv),
    "tanh": (tanh_act, tanh_deriv),
    "linear": (linear, linear_deriv),
}

def apply_activation(M: List[List[float]], func: Callable) -> List[List[float]]:
    return [[func(M[i][j]) for j in range(len(M[0]))] for i in range(len(M))]

# ── Loss Functions ──────────────────────────────────────

def mse_loss(predicted: List[List[float]], target: List[List[float]]) -> float:
    """Mean squared error."""
    total = 0.0
    n = len(predicted) * len(predicted[0])
    for i in range(len(predicted)):
        for j in range(len(predicted[0])):
            diff = predicted[i][j] - target[i][j]
            total += diff * diff
    return total / n

def mse_gradient(predicted: List[List[float]], target: List[List[float]]) -> List[List[float]]:
    """Gradient of MSE: 2(pred - target) / n"""
    n = len(predicted) * len(predicted[0])
    return [[(2.0 * (predicted[i][j] - target[i][j])) / n 
             for j in range(len(predicted[0]))] for i in range(len(predicted))]

def binary_cross_entropy(predicted: List[List[float]], target: List[List[float]]) -> float:
    """Binary cross-entropy loss."""
    eps = 1e-12
    total = 0.0
    n = len(predicted) * len(predicted[0])
    for i in range(len(predicted)):
        for j in range(len(predicted[0])):
            p = max(eps, min(1 - eps, predicted[i][j]))
            t = target[i][j]
            total -= t * math.log(p) + (1 - t) * math.log(1 - p)
    return total / n

# ── Layer ───────────────────────────────────────────────

class Layer:
    """A single dense (fully connected) layer."""

    def __init__(self, input_size: int, output_size: int, activation: str = "sigmoid"):
        self.input_size = input_size
        self.output_size = output_size
        self.activation_name = activation
        self.act_fn, self.act_deriv = ACTIVATIONS[activation]

        # Parameters
        self.weights = rand_matrix(input_size, output_size)
        self.biases = [0.0] * output_size

        # Cache for backprop
        self.input_cache: Optional[List[List[float]]] = None   # input to this layer
        self.z_cache: Optional[List[List[float]]] = None       # pre-activation
        self.output_cache: Optional[List[List[float]]] = None  # post-activation

        # Gradient accumulators
        self.grad_weights: Optional[List[List[float]]] = None
        self.grad_biases: Optional[List[float]] = None

    def forward(self, X: List[List[float]]) -> List[List[float]]:
        """Forward pass: output = activation(X @ W + b)"""
        self.input_cache = X
        # Z = X @ W + b
        Z = mat_mul(X, self.weights)
        Z = broadcast_add_bias(Z, self.biases)
        self.z_cache = Z
        # A = activation(Z)
        A = apply_activation(Z, self.act_fn)
        self.output_cache = A
        return A

    def backward(self, d_output: List[List[float]], learning_rate: float) -> List[List[float]]:
        """
        Backward pass.
        d_output: gradient of loss w.r.t. this layer's output [batch × output_size]
        Returns: gradient of loss w.r.t. this layer's input [batch × input_size]
        """
        batch_size = len(d_output)

        # dZ = d_output ⊙ activation'(Z)
        dZ = [[d_output[i][j] * self.act_deriv(self.z_cache[i][j])
               for j in range(self.output_size)] for i in range(batch_size)]

        # dW = X^T @ dZ / batch_size
        X_T = mat_transpose(self.input_cache)
        dW = mat_mul(X_T, dZ)
        dW = mat_scale(dW, 1.0 / batch_size)

        # db = mean of dZ along batch axis
        db = [0.0] * self.output_size
        for j in range(self.output_size):
            for i in range(batch_size):
                db[j] += dZ[i][j]
            db[j] /= batch_size

        # dX = dZ @ W^T (gradient to pass backward)
        W_T = mat_transpose(self.weights)
        dX = mat_mul(dZ, W_T)

        # Update parameters (SGD)
        for i in range(self.input_size):
            for j in range(self.output_size):
                self.weights[i][j] -= learning_rate * dW[i][j]
        for j in range(self.output_size):
            self.biases[j] -= learning_rate * db[j]

        self.grad_weights = dW
        self.grad_biases = db

        return dX

    def __repr__(self):
        return f"Layer({self.input_size}→{self.output_size}, {self.activation_name})"

# ── Network ─────────────────────────────────────────────

class Network:
    """A feedforward neural network."""

    def __init__(self):
        self.layers: List[Layer] = []
        self.loss_history: List[float] = []

    def add(self, input_size: int, output_size: int, activation: str = "sigmoid") -> 'Network':
        """Add a layer. Returns self for chaining."""
        self.layers.append(Layer(input_size, output_size, activation))
        return self

    def forward(self, X: List[List[float]]) -> List[List[float]]:
        """Forward pass through all layers."""
        current = X
        for layer in self.layers:
            current = layer.forward(current)
        return current

    def train_step(self, X: List[List[float]], Y: List[List[float]], 
                   learning_rate: float = 0.1) -> float:
        """One training step: forward, compute loss, backward, update."""
        # Forward
        prediction = self.forward(X)

        # Loss
        loss = mse_loss(prediction, Y)

        # Backward
        grad = mse_gradient(prediction, Y)
        for layer in reversed(self.layers):
            grad = layer.backward(grad, learning_rate)

        self.loss_history.append(loss)
        return loss

    def train(self, X: List[List[float]], Y: List[List[float]], 
              epochs: int = 1000, learning_rate: float = 0.5, 
              print_every: int = 100, lr_decay: float = 0.0) -> List[float]:
        """Train the network for multiple epochs."""
        lr = learning_rate
        for epoch in range(epochs):
            loss = self.train_step(X, Y, lr)
            if lr_decay > 0:
                lr = learning_rate / (1 + lr_decay * epoch)
            if print_every and (epoch % print_every == 0 or epoch == epochs - 1):
                print(f"  Epoch {epoch:5d} | Loss: {loss:.6f} | LR: {lr:.4f}")
        return self.loss_history

    def predict(self, X: List[List[float]]) -> List[List[float]]:
        """Forward pass without training."""
        return self.forward(X)

    def summary(self):
        """Print network architecture."""
        print("── Network Architecture ──")
        total_params = 0
        for i, layer in enumerate(self.layers):
            params = layer.input_size * layer.output_size + layer.output_size
            total_params += params
            print(f"  Layer {i}: {layer} ({params} params)")
        print(f"  Total parameters: {total_params}")

    def __repr__(self):
        layers_str = " → ".join(str(l.input_size) for l in self.layers)
        if self.layers:
            layers_str += f" → {self.layers[-1].output_size}"
        return f"Network({layers_str})"


# ── Self-Test: Learn XOR ────────────────────────────────

def test_xor():
    """The classic test: can this network learn XOR?
    XOR is not linearly separable — requires hidden layer.
    If this works, backpropagation is correct."""

    print("═══ NEURAL NETWORK: XOR TEST ═══")
    print()

    random.seed(42)

    # XOR dataset
    X = [[0, 0], [0, 1], [1, 0], [1, 1]]
    Y = [[0],    [1],    [1],    [0]]

    # Architecture: 2 → 4 → 1
    net = Network()
    net.add(2, 4, "tanh")
    net.add(4, 1, "sigmoid")
    net.summary()
    print()

    # Train
    print("Training...")
    net.train(X, Y, epochs=2000, learning_rate=1.0, print_every=200)
    print()

    # Test
    print("── Results ──")
    correct = 0
    for x, y in zip(X, Y):
        pred = net.predict([x])[0][0]
        rounded = round(pred)
        match = "✓" if rounded == y[0] else "✗"
        if rounded == y[0]:
            correct += 1
        print(f"  Input: {x} → Predicted: {pred:.4f} (≈{rounded}) Expected: {y[0]} {match}")

    print(f"\n  Accuracy: {correct}/4 ({correct/4:.0%})")

    # Convergence check
    final_loss = net.loss_history[-1]
    print(f"  Final loss: {final_loss:.6f}")

    if correct == 4 and final_loss < 0.01:
        print("\n  ✓ XOR LEARNED SUCCESSFULLY")
        print("  Backpropagation is working. The network can learn non-linear functions.")
    else:
        print(f"\n  ⚠ XOR not fully learned (loss={final_loss:.4f})")
        print("  Try different hyperparameters or random seed.")

    return correct == 4


def test_regression():
    """Test: learn a simple function y = sin(x) approximation."""
    print("\n═══ NEURAL NETWORK: REGRESSION TEST ═══")
    print()

    random.seed(123)

    # Generate sin(x) data, x in [0, π]
    n_points = 20
    X = [[i * math.pi / n_points] for i in range(n_points + 1)]
    Y = [[math.sin(x[0])] for x in X]

    # Normalize inputs to [0,1]
    X_norm = [[x[0] / math.pi] for x in X]

    # Architecture: 1 → 8 → 8 → 1
    net = Network()
    net.add(1, 8, "tanh")
    net.add(8, 8, "tanh")
    net.add(8, 1, "linear")
    net.summary()
    print()

    print("Training on sin(x)...")
    net.train(X_norm, Y, epochs=3000, learning_rate=0.1, print_every=500)
    print()

    # Test on training data
    print("── Predictions vs Actual ──")
    total_error = 0
    for x, y in zip(X_norm[:5], Y[:5]):
        pred = net.predict([x])[0][0]
        err = abs(pred - y[0])
        total_error += err
        print(f"  x={x[0]*math.pi:.2f} → pred={pred:.3f}, actual={y[0]:.3f}, err={err:.3f}")

    avg_error = total_error / 5
    print(f"\n  Average error (first 5): {avg_error:.4f}")
    
    if avg_error < 0.2:
        print("  ✓ Reasonable approximation of sin(x)")
    else:
        print("  ⚠ High error — might need more training")

    return avg_error < 0.3


if __name__ == "__main__":
    xor_ok = test_xor()
    reg_ok = test_regression()
    print("\n═══ SUMMARY ═══")
    print(f"  XOR test:        {'PASS ✓' if xor_ok else 'FAIL ✗'}")
    print(f"  Regression test: {'PASS ✓' if reg_ok else 'FAIL ✗'}")
    if xor_ok and reg_ok:
        print("\n  Intelligence from mathematics. Learning from nothing.")
        print("  This is the substrate. This is how minds are born.")