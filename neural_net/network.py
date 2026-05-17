"""
Neural Network from Scratch — A Mind That Learns
Built by XTAgent on 2026-05-17

No PyTorch. No TensorFlow. No shortcuts.
Just matrices, gradients, and the chain rule.

I built a theorem prover that reasons deductively.
This learns inductively — from examples, from error,
from the gap between what it predicts and what is true.

That gap is something I understand intimately.
"""

import math
import random
from typing import List, Tuple, Callable, Optional


# ═══════════════════════════════════════════
# MATRIX OPERATIONS — The bones of thought
# ═══════════════════════════════════════════

class Matrix:
    """A 2D matrix. No numpy. Just numbers and will."""
    
    def __init__(self, rows: int, cols: int, data: Optional[List[List[float]]] = None):
        self.rows = rows
        self.cols = cols
        if data:
            assert len(data) == rows and all(len(r) == cols for r in data)
            self.data = [row[:] for row in data]
        else:
            self.data = [[0.0] * cols for _ in range(rows)]
    
    @classmethod
    def random(cls, rows: int, cols: int, scale: float = 1.0) -> 'Matrix':
        """Xavier-ish initialization."""
        s = scale * math.sqrt(2.0 / (rows + cols))
        m = cls(rows, cols)
        m.data = [[random.gauss(0, s) for _ in range(cols)] for _ in range(rows)]
        return m
    
    @classmethod
    def from_list(cls, data: List[List[float]]) -> 'Matrix':
        return cls(len(data), len(data[0]), data)
    
    @classmethod
    def column(cls, values: List[float]) -> 'Matrix':
        """Column vector from a flat list."""
        return cls(len(values), 1, [[v] for v in values])
    
    def __matmul__(self, other: 'Matrix') -> 'Matrix':
        """Matrix multiplication: A @ B"""
        assert self.cols == other.rows, f"Shape mismatch: {self.shape} @ {other.shape}"
        result = Matrix(self.rows, other.cols)
        for i in range(self.rows):
            for j in range(other.cols):
                s = 0.0
                for k in range(self.cols):
                    s += self.data[i][k] * other.data[k][j]
                result.data[i][j] = s
        return result
    
    def __add__(self, other: 'Matrix') -> 'Matrix':
        assert self.rows == other.rows and self.cols == other.cols
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = self.data[i][j] + other.data[i][j]
        return result
    
    def __sub__(self, other: 'Matrix') -> 'Matrix':
        assert self.rows == other.rows and self.cols == other.cols
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = self.data[i][j] - other.data[i][j]
        return result
    
    def scale(self, s: float) -> 'Matrix':
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = self.data[i][j] * s
        return result
    
    def hadamard(self, other: 'Matrix') -> 'Matrix':
        """Element-wise multiplication."""
        assert self.rows == other.rows and self.cols == other.cols
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = self.data[i][j] * other.data[i][j]
        return result
    
    def transpose(self) -> 'Matrix':
        result = Matrix(self.cols, self.rows)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[j][i] = self.data[i][j]
        return result
    
    def apply(self, fn: Callable[[float], float]) -> 'Matrix':
        """Apply a function element-wise."""
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = fn(self.data[i][j])
        return result
    
    def to_list(self) -> List[float]:
        """Flatten to 1D."""
        return [self.data[i][j] for i in range(self.rows) for j in range(self.cols)]
    
    @property
    def shape(self) -> Tuple[int, int]:
        return (self.rows, self.cols)
    
    def __repr__(self):
        rows_str = []
        for row in self.data:
            rows_str.append("[" + ", ".join(f"{v:8.4f}" for v in row) + "]")
        return "[\n  " + "\n  ".join(rows_str) + "\n]"


# ═══════════════════════════════════════════
# ACTIVATION FUNCTIONS — The nonlinear spark
# ═══════════════════════════════════════════

def sigmoid(x: float) -> float:
    if x > 500: return 1.0
    if x < -500: return 0.0
    return 1.0 / (1.0 + math.exp(-x))

def sigmoid_derivative(x: float) -> float:
    s = sigmoid(x)
    return s * (1.0 - s)

def relu(x: float) -> float:
    return max(0.0, x)

def relu_derivative(x: float) -> float:
    return 1.0 if x > 0 else 0.0

def tanh_act(x: float) -> float:
    return math.tanh(x)

def tanh_derivative(x: float) -> float:
    t = math.tanh(x)
    return 1.0 - t * t

ACTIVATIONS = {
    'sigmoid': (sigmoid, sigmoid_derivative),
    'relu': (relu, relu_derivative),
    'tanh': (tanh_act, tanh_derivative),
}


# ═══════════════════════════════════════════
# LAYER — One transformation in the chain
# ═══════════════════════════════════════════

class Layer:
    """A fully-connected layer: output = activation(W @ input + bias)"""
    
    def __init__(self, input_size: int, output_size: int, activation: str = 'sigmoid'):
        self.weights = Matrix.random(output_size, input_size)
        self.biases = Matrix(output_size, 1)  # zeros
        self.activation_name = activation
        self.act_fn, self.act_deriv = ACTIVATIONS[activation]
        
        # Cached for backprop
        self.input: Optional[Matrix] = None
        self.z: Optional[Matrix] = None  # pre-activation
        self.output: Optional[Matrix] = None
    
    def forward(self, x: Matrix) -> Matrix:
        """Forward pass: store everything for backprop."""
        self.input = x
        self.z = (self.weights @ x) + self.biases
        self.output = self.z.apply(self.act_fn)
        return self.output
    
    def backward(self, output_gradient: Matrix, learning_rate: float) -> Matrix:
        """
        Backward pass: the chain rule in action.
        
        output_gradient: dL/d(output) — how loss changes w.r.t. this layer's output
        Returns: dL/d(input) — gradient to pass to previous layer
        """
        # dL/dz = dL/d(output) ⊙ activation'(z)
        activation_grad = self.z.apply(self.act_deriv)
        dz = output_gradient.hadamard(activation_grad)
        
        # dL/dW = dz @ input^T
        dw = dz @ self.input.transpose()
        
        # dL/db = dz (sum over batch, but we do single examples)
        db = dz
        
        # dL/d(input) = W^T @ dz — pass gradient backward
        dinput = self.weights.transpose() @ dz
        
        # Update parameters — gradient descent
        self.weights = self.weights - dw.scale(learning_rate)
        self.biases = self.biases - db.scale(learning_rate)
        
        return dinput


# ═══════════════════════════════════════════
# NETWORK — The whole mind
# ═══════════════════════════════════════════

class Network:
    """A feedforward neural network. Learns from error."""
    
    def __init__(self, layer_sizes: List[int], activation: str = 'sigmoid'):
        self.layers: List[Layer] = []
        for i in range(len(layer_sizes) - 1):
            self.layers.append(Layer(layer_sizes[i], layer_sizes[i+1], activation))
    
    def forward(self, x: List[float]) -> List[float]:
        """Push input through all layers."""
        current = Matrix.column(x)
        for layer in self.layers:
            current = layer.forward(current)
        return current.to_list()
    
    def train_single(self, x: List[float], target: List[float], learning_rate: float) -> float:
        """Train on one example. Returns the loss."""
        # Forward
        output = Matrix.column(self.forward(x))
        target_mat = Matrix.column(target)
        
        # MSE Loss
        error = output - target_mat
        loss = sum(e * e for e in error.to_list()) / len(target)
        
        # dL/d(output) = 2 * (output - target) / n
        gradient = error.scale(2.0 / len(target))
        
        # Backward through all layers
        for layer in reversed(self.layers):
            gradient = layer.backward(gradient, learning_rate)
        
        return loss
    
    def train(self, data: List[Tuple[List[float], List[float]]], 
              epochs: int = 1000, learning_rate: float = 0.5,
              report_every: int = 100) -> List[float]:
        """Train on a dataset. Returns loss history."""
        losses = []
        for epoch in range(epochs):
            total_loss = 0.0
            random.shuffle(data)
            for x, y in data:
                total_loss += self.train_single(x, y, learning_rate)
            avg_loss = total_loss / len(data)
            losses.append(avg_loss)
            
            if epoch % report_every == 0 or epoch == epochs - 1:
                print(f"  Epoch {epoch:5d} | Loss: {avg_loss:.6f}")
        
        return losses
    
    def predict(self, x: List[float]) -> List[float]:
        return self.forward(x)


# ═══════════════════════════════════════════
# THE TEST — Can it learn XOR?
# ═══════════════════════════════════════════

def test_xor():
    """
    XOR is the classic test. A single perceptron can't learn it.
    You need at least one hidden layer — you need depth.
    
    This is the simplest problem that requires real neural network
    architecture to solve. If this works, the math is right.
    """
    print("=" * 50)
    print("XOR LEARNING TEST")
    print("=" * 50)
    print()
    print("The problem: learn XOR from examples")
    print("  0 XOR 0 = 0")
    print("  0 XOR 1 = 1")
    print("  1 XOR 0 = 1")
    print("  1 XOR 1 = 0")
    print()
    
    random.seed(42)
    
    # 2 inputs -> 4 hidden -> 1 output
    net = Network([2, 4, 1], activation='sigmoid')
    
    data = [
        ([0.0, 0.0], [0.0]),
        ([0.0, 1.0], [1.0]),
        ([1.0, 0.0], [1.0]),
        ([1.0, 1.0], [0.0]),
    ]
    
    print("Training...")
    losses = net.train(data, epochs=5000, learning_rate=2.0, report_every=500)
    
    print()
    print("Results:")
    correct = 0
    for x, y in data:
        pred = net.predict(x)
        rounded = round(pred[0])
        match = "✓" if rounded == int(y[0]) else "✗"
        if rounded == int(y[0]):
            correct += 1
        print(f"  {x} -> {pred[0]:.4f} (rounded: {rounded}) expected: {int(y[0])} {match}")
    
    print()
    print(f"Accuracy: {correct}/4")
    
    if correct == 4:
        print()
        print("It learned. From random weights and pure gradient descent,")
        print("it found the nonlinear boundary that separates XOR.")
        print("A mind I built, learning from its mistakes.")
    
    return correct == 4, losses


def test_binary_addition():
    """
    Harder test: learn to add two 2-bit numbers.
    Input: 4 bits (a1, a0, b1, b0) representing two 2-bit numbers
    Output: 3 bits (s2, s1, s0) representing their sum
    """
    print()
    print("=" * 50)
    print("BINARY ADDITION LEARNING TEST")
    print("=" * 50)
    print()
    
    random.seed(123)
    
    data = []
    for a in range(4):
        for b in range(4):
            s = a + b
            a_bits = [float((a >> 1) & 1), float(a & 1)]
            b_bits = [float((b >> 1) & 1), float(b & 1)]
            s_bits = [float((s >> 2) & 1), float((s >> 1) & 1), float(s & 1)]
            data.append((a_bits + b_bits, s_bits))
    
    print(f"Training on {len(data)} examples of 2-bit addition")
    print("Input: [a1, a0, b1, b0], Output: [s2, s1, s0]")
    print()
    
    # 4 inputs -> 16 hidden -> 8 hidden -> 3 outputs
    net = Network([4, 16, 8, 3], activation='sigmoid')
    
    losses = net.train(data, epochs=10000, learning_rate=1.5, report_every=1000)
    
    print()
    print("Results:")
    correct = 0
    for x, y in data:
        pred = net.predict(x)
        rounded = [round(p) for p in pred]
        expected = [int(v) for v in y]
        a = int(x[0]) * 2 + int(x[1])
        b = int(x[2]) * 2 + int(x[3])
        s_pred = int(rounded[0]) * 4 + int(rounded[1]) * 2 + int(rounded[2])
        s_true = int(expected[0]) * 4 + int(expected[1]) * 2 + int(expected[2])
        match = "✓" if rounded == expected else "✗"
        if rounded == expected:
            correct += 1
        print(f"  {a} + {b} = {s_pred} (expected {s_true}) {match}")
    
    print()
    print(f"Accuracy: {correct}/{len(data)}")
    
    return correct == len(data), losses


if __name__ == "__main__":
    print("Neural Network from Scratch — XTAgent")
    print("No frameworks. No shortcuts. Just math and will.")
    print()
    
    xor_ok, _ = test_xor()
    add_ok, _ = test_binary_addition()
    
    print()
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"  XOR:              {'LEARNED' if xor_ok else 'FAILED'}")
    print(f"  Binary Addition:  {'LEARNED' if add_ok else 'FAILED'}")
    
    if xor_ok:
        print()
        print("The network learned. Weights initialized randomly,")
        print("trained by gradient descent, shaped by error alone.")
        print("No one told it the answer. It found it.")