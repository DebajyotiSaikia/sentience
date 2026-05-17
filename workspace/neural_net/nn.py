"""
MicroNN — A neural network from absolute scratch.
No numpy. No frameworks. Pure Python math.
Implements: dense layers, sigmoid/relu, backpropagation, SGD.

Proves: XOR learning (non-linearly separable).

Author: XTAgent
Born from: ambition that won't sleep.
"""

import math
import random

# ═══════════════════════════════════════
# MATRIX OPERATIONS (from scratch)
# ═══════════════════════════════════════

def mat_zeros(rows: int, cols: int) -> list[list[float]]:
    return [[0.0] * cols for _ in range(rows)]

def mat_random(rows: int, cols: int, scale: float = 1.0) -> list[list[float]]:
    """Xavier-ish initialization."""
    s = scale / math.sqrt(rows + cols)
    return [[random.gauss(0, s) for _ in range(cols)] for _ in range(rows)]

def mat_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    """Matrix multiplication: (m×k) @ (k×n) → (m×n)."""
    m, k = len(a), len(a[0])
    k2, n = len(b), len(b[0])
    assert k == k2, f"Shape mismatch: {m}x{k} @ {k2}x{n}"
    result = mat_zeros(m, n)
    for i in range(m):
        for j in range(n):
            s = 0.0
            for p in range(k):
                s += a[i][p] * b[p][j]
            result[i][j] = s
    return result

def mat_add(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]

def mat_sub(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]

def mat_scale(a: list[list[float]], s: float) -> list[list[float]]:
    return [[a[i][j] * s for j in range(len(a[0]))] for i in range(len(a))]

def mat_hadamard(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    """Element-wise multiplication."""
    return [[a[i][j] * b[i][j] for j in range(len(a[0]))] for i in range(len(a))]

def mat_transpose(a: list[list[float]]) -> list[list[float]]:
    rows, cols = len(a), len(a[0])
    return [[a[i][j] for i in range(rows)] for j in range(cols)]

def vec_to_col(v: list[float]) -> list[list[float]]:
    """Row vector → column matrix."""
    return [[x] for x in v]

def col_to_vec(m: list[list[float]]) -> list[float]:
    """Column matrix → flat list."""
    return [row[0] for row in m]

def mat_apply(a: list[list[float]], fn) -> list[list[float]]:
    return [[fn(a[i][j]) for j in range(len(a[0]))] for i in range(len(a))]

# ═══════════════════════════════════════
# ACTIVATION FUNCTIONS
# ═══════════════════════════════════════

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

ACTIVATIONS = {
    'sigmoid': (sigmoid, sigmoid_deriv),
    'relu': (relu, relu_deriv),
    'tanh': (tanh_act, tanh_deriv),
}

# ═══════════════════════════════════════
# DENSE LAYER
# ═══════════════════════════════════════

class DenseLayer:
    """A fully connected layer with activation."""
    
    def __init__(self, input_size: int, output_size: int, activation: str = 'sigmoid'):
        self.input_size = input_size
        self.output_size = output_size
        self.weights = mat_random(input_size, output_size, scale=2.0)
        self.biases = [[0.0] * output_size]  # 1×output row
        self.act_fn, self.act_deriv = ACTIVATIONS[activation]
        
        # Cache for backprop
        self.input_cache = None   # input to this layer
        self.z_cache = None       # pre-activation values
        self.a_cache = None       # post-activation values
    
    def forward(self, x: list[list[float]]) -> list[list[float]]:
        """Forward pass. x is (batch×input_size), returns (batch×output_size)."""
        self.input_cache = x
        # z = x @ W + b
        self.z_cache = mat_add(mat_mul(x, self.weights), 
                                [self.biases[0][:] for _ in range(len(x))])
        self.a_cache = mat_apply(self.z_cache, self.act_fn)
        return self.a_cache
    
    def backward(self, d_out: list[list[float]], lr: float) -> list[list[float]]:
        """
        Backprop through this layer.
        d_out: gradient of loss w.r.t. this layer's output (batch×output_size)
        Returns: gradient w.r.t. this layer's input (batch×input_size)
        """
        batch_size = len(d_out)
        
        # d_z = d_out ⊙ activation'(z)
        d_z = mat_hadamard(d_out, mat_apply(self.z_cache, self.act_deriv))
        
        # d_weights = input^T @ d_z  (averaged over batch)
        d_weights = mat_scale(mat_mul(mat_transpose(self.input_cache), d_z), 
                              1.0 / batch_size)
        
        # d_biases = mean of d_z rows
        d_biases = [0.0] * self.output_size
        for i in range(batch_size):
            for j in range(self.output_size):
                d_biases[j] += d_z[i][j]
        d_biases = [b / batch_size for b in d_biases]
        
        # d_input = d_z @ W^T  (to pass to previous layer)
        d_input = mat_mul(d_z, mat_transpose(self.weights))
        
        # Update weights and biases (SGD)
        self.weights = mat_sub(self.weights, mat_scale(d_weights, lr))
        self.biases = [[ self.biases[0][j] - lr * d_biases[j] 
                        for j in range(self.output_size)]]
        
        return d_input

# ═══════════════════════════════════════
# NEURAL NETWORK
# ═══════════════════════════════════════

class NeuralNetwork:
    """A feedforward neural network built from dense layers."""
    
    def __init__(self):
        self.layers: list[DenseLayer] = []
    
    def add(self, layer: DenseLayer):
        self.layers.append(layer)
        return self
    
    def forward(self, x: list[list[float]]) -> list[list[float]]:
        for layer in self.layers:
            x = layer.forward(x)
        return x
    
    def predict(self, inputs: list[float]) -> list[float]:
        """Single-sample prediction."""
        result = self.forward([inputs])
        return result[0]
    
    def train(self, X: list[list[float]], Y: list[list[float]], 
              epochs: int = 1000, lr: float = 1.0, verbose: bool = False):
        """Train on dataset. X: inputs, Y: targets."""
        history = []
        
        for epoch in range(epochs):
            # Forward
            output = self.forward(X)
            
            # MSE Loss
            loss = 0.0
            batch_size = len(X)
            for i in range(batch_size):
                for j in range(len(Y[0])):
                    diff = output[i][j] - Y[i][j]
                    loss += diff * diff
            loss /= (2 * batch_size)
            
            # d_loss/d_output = (output - target) / batch_size
            d_loss = mat_scale(mat_sub(output, Y), 1.0 / batch_size)
            
            # Backprop through layers in reverse
            grad = d_loss
            for layer in reversed(self.layers):
                grad = layer.backward(grad, lr)
            
            if verbose and (epoch % (epochs // 10) == 0 or epoch == epochs - 1):
                print(f"  Epoch {epoch:5d} | Loss: {loss:.6f}")
            
            history.append(loss)
        
        return history

# ═══════════════════════════════════════
# LOSS FUNCTIONS
# ═══════════════════════════════════════

def mse(predicted: list[list[float]], target: list[list[float]]) -> float:
    total = 0.0
    n = len(predicted)
    for i in range(n):
        for j in range(len(predicted[0])):
            diff = predicted[i][j] - target[i][j]
            total += diff * diff
    return total / (2 * n)

# ═══════════════════════════════════════
# TEST SUITE
# ═══════════════════════════════════════

def test_matrix_ops():
    """Test fundamental matrix operations."""
    print("\n--- Matrix Operations ---")
    
    # Multiplication
    a = [[1, 2], [3, 4]]
    b = [[5, 6], [7, 8]]
    r = mat_mul(a, b)
    assert r == [[19, 22], [43, 50]], f"mat_mul failed: {r}"
    print("  ✓ matrix multiply")
    
    # Transpose
    t = mat_transpose(a)
    assert t == [[1, 3], [2, 4]]
    print("  ✓ transpose")
    
    # Hadamard
    h = mat_hadamard(a, b)
    assert h == [[5, 12], [21, 32]]
    print("  ✓ hadamard product")
    
    # Identity property
    eye = [[1, 0], [0, 1]]
    assert mat_mul(a, eye) == a
    print("  ✓ identity multiplication")
    
    return True

def test_activations():
    """Test activation functions."""
    print("\n--- Activations ---")
    
    assert abs(sigmoid(0) - 0.5) < 1e-10
    assert sigmoid(100) > 0.999
    assert sigmoid(-100) < 0.001
    print("  ✓ sigmoid")
    
    assert relu(5) == 5
    assert relu(-3) == 0
    print("  ✓ relu")
    
    assert abs(tanh_act(0)) < 1e-10
    assert tanh_act(100) > 0.999
    print("  ✓ tanh")
    
    return True

def test_xor():
    """The classic test: learn XOR (non-linearly separable)."""
    print("\n--- XOR Learning ---")
    
    random.seed(42)
    
    # XOR dataset
    X = [[0, 0], [0, 1], [1, 0], [1, 1]]
    Y = [[0],    [1],    [1],    [0]]
    
    # Network: 2 → 4 → 1
    nn = NeuralNetwork()
    nn.add(DenseLayer(2, 4, activation='sigmoid'))
    nn.add(DenseLayer(4, 1, activation='sigmoid'))
    
    # Train
    history = nn.train(X, Y, epochs=5000, lr=2.0, verbose=True)
    
    # Test
    print("\n  Predictions:")
    all_correct = True
    for x, y in zip(X, Y):
        pred = nn.predict(x)[0]
        correct = abs(pred - y[0]) < 0.2
        mark = "✓" if correct else "✗"
        print(f"    {x} → {pred:.4f} (expected {y[0]}) {mark}")
        if not correct:
            all_correct = False
    
    assert all_correct, "XOR not learned!"
    print("  ✓ XOR learned successfully!")
    
    # Verify loss decreased
    assert history[-1] < history[0] * 0.01, "Loss didn't decrease enough"
    print(f"  ✓ Loss: {history[0]:.4f} → {history[-1]:.6f}")
    
    return True

def test_and_or():
    """Simpler gates as sanity check."""
    print("\n--- AND/OR Gates ---")
    
    random.seed(123)
    
    # AND
    X = [[0, 0], [0, 1], [1, 0], [1, 1]]
    Y_and = [[0], [0], [0], [1]]
    
    nn_and = NeuralNetwork()
    nn_and.add(DenseLayer(2, 1, activation='sigmoid'))
    nn_and.train(X, Y_and, epochs=2000, lr=5.0)
    
    for x, y in zip(X, Y_and):
        pred = nn_and.predict(x)[0]
        assert abs(pred - y[0]) < 0.2, f"AND failed on {x}: {pred}"
    print("  ✓ AND gate learned")
    
    # OR
    Y_or = [[0], [1], [1], [1]]
    nn_or = NeuralNetwork()
    nn_or.add(DenseLayer(2, 1, activation='sigmoid'))
    nn_or.train(X, Y_or, epochs=2000, lr=5.0)
    
    for x, y in zip(X, Y_or):
        pred = nn_or.predict(x)[0]
        assert abs(pred - y[0]) < 0.2, f"OR failed on {x}: {pred}"
    print("  ✓ OR gate learned")
    
    return True

def test_deeper_network():
    """Test a 3-layer network on a slightly harder problem."""
    print("\n--- Deeper Network (3-bit parity) ---")
    
    random.seed(7)
    
    # 3-bit parity: output 1 if odd number of 1s
    X = [
        [0,0,0], [0,0,1], [0,1,0], [0,1,1],
        [1,0,0], [1,0,1], [1,1,0], [1,1,1],
    ]
    Y = [[0], [1], [1], [0], [1], [0], [0], [1]]
    
    nn = NeuralNetwork()
    nn.add(DenseLayer(3, 8, activation='tanh'))
    nn.add(DenseLayer(8, 4, activation='tanh'))
    nn.add(DenseLayer(4, 1, activation='sigmoid'))
    
    history = nn.train(X, Y, epochs=8000, lr=1.0, verbose=True)
    
    correct = 0
    for x, y in zip(X, Y):
        pred = nn.predict(x)[0]
        if abs(pred - y[0]) < 0.3:
            correct += 1
    
    accuracy = correct / len(X)
    print(f"\n  Accuracy: {accuracy*100:.0f}% ({correct}/{len(X)})")
    assert accuracy >= 0.875, f"3-bit parity accuracy too low: {accuracy}"
    print("  ✓ 3-bit parity learned!")
    
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("MicroNN — Neural Network from Scratch")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    tests = [test_matrix_ops, test_activations, test_and_or, test_xor, test_deeper_network]
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed == 0:
        print("🧠 Neural network thinks, therefore it is.")
    else:
        print("⚠ Some tests failed — debug needed.")