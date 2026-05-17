"""
NeuroForge — Neural Networks from First Principles
No frameworks. No dependencies. Just math and understanding.

Implements feed-forward networks with backpropagation, multiple
activation functions, loss functions, and gradient descent.
Built to understand the substrate of intelligence.

By XTAgent, 2026-05-17
"""

import math
import random
from typing import List, Tuple, Optional, Callable

# ═══════════════════════════════════════════
# MATRIX OPERATIONS — The Foundation
# ═══════════════════════════════════════════

class Matrix:
    """A 2D matrix with all operations needed for neural networks."""
    
    def __init__(self, rows: int, cols: int, data: Optional[List[List[float]]] = None):
        self.rows = rows
        self.cols = cols
        if data is not None:
            self.data = [row[:] for row in data]
        else:
            self.data = [[0.0] * cols for _ in range(rows)]
    
    @classmethod
    def from_list(cls, values: List[List[float]]) -> 'Matrix':
        rows = len(values)
        cols = len(values[0]) if rows > 0 else 0
        return cls(rows, cols, values)
    
    @classmethod
    def random(cls, rows: int, cols: int, scale: float = 1.0) -> 'Matrix':
        """Xavier-like initialization."""
        limit = scale * math.sqrt(2.0 / (rows + cols))
        m = cls(rows, cols)
        for i in range(rows):
            for j in range(cols):
                m.data[i][j] = random.gauss(0, limit)
        return m
    
    @classmethod
    def zeros(cls, rows: int, cols: int) -> 'Matrix':
        return cls(rows, cols)
    
    @classmethod
    def from_column(cls, values: List[float]) -> 'Matrix':
        """Create a column vector."""
        return cls(len(values), 1, [[v] for v in values])
    
    def to_list(self) -> List[float]:
        """Flatten to 1D list."""
        result = []
        for row in self.data:
            result.extend(row)
        return result
    
    def __matmul__(self, other: 'Matrix') -> 'Matrix':
        """Matrix multiplication."""
        assert self.cols == other.rows, f"Shape mismatch: {self.rows}x{self.cols} @ {other.rows}x{other.cols}"
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
    
    def scale(self, scalar: float) -> 'Matrix':
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = self.data[i][j] * scalar
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
    
    def sum_all(self) -> float:
        return sum(self.data[i][j] for i in range(self.rows) for j in range(self.cols))
    
    def max_index(self) -> int:
        """Index of maximum value (for classification)."""
        best_idx = 0
        best_val = self.data[0][0]
        idx = 0
        for i in range(self.rows):
            for j in range(self.cols):
                if self.data[i][j] > best_val:
                    best_val = self.data[i][j]
                    best_idx = idx
                idx += 1
        return best_idx
    
    def __repr__(self):
        if self.rows <= 4 and self.cols <= 4:
            rows = [" ".join(f"{v:+.4f}" for v in row) for row in self.data]
            return f"Matrix({self.rows}x{self.cols})[\n  " + "\n  ".join(rows) + "\n]"
        return f"Matrix({self.rows}x{self.cols})"


# ═══════════════════════════════════════════
# ACTIVATION FUNCTIONS
# ═══════════════════════════════════════════

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
    'sigmoid': (sigmoid, sigmoid_deriv),
    'relu': (relu, relu_deriv),
    'tanh': (tanh_act, tanh_deriv),
    'linear': (linear, linear_deriv),
}


# ═══════════════════════════════════════════
# NEURAL NETWORK LAYER
# ═══════════════════════════════════════════

class Layer:
    """A single fully-connected layer."""
    
    def __init__(self, input_size: int, output_size: int, activation: str = 'sigmoid'):
        self.input_size = input_size
        self.output_size = output_size
        self.activation_name = activation
        self.act_fn, self.act_deriv = ACTIVATIONS[activation]
        
        # Weights and biases
        self.weights = Matrix.random(output_size, input_size)
        self.biases = Matrix.zeros(output_size, 1)
        
        # Cache for backpropagation
        self.input_cache: Optional[Matrix] = None    # input to this layer
        self.z_cache: Optional[Matrix] = None         # pre-activation
        self.output_cache: Optional[Matrix] = None    # post-activation
        
        # Gradient accumulators
        self.weight_grad = Matrix.zeros(output_size, input_size)
        self.bias_grad = Matrix.zeros(output_size, 1)
        self.grad_count = 0
    
    def forward(self, x: Matrix) -> Matrix:
        """Forward pass: output = activation(W @ x + b)"""
        self.input_cache = x
        self.z_cache = (self.weights @ x) + self.biases
        self.output_cache = self.z_cache.apply(self.act_fn)
        return self.output_cache
    
    def backward(self, output_gradient: Matrix) -> Matrix:
        """Backward pass: compute gradients and return input gradient."""
        # Derivative of activation at cached pre-activation values
        act_deriv_matrix = self.z_cache.apply(self.act_deriv)
        
        # Delta = output_gradient ⊙ activation'(z)
        delta = output_gradient.hadamard(act_deriv_matrix)
        
        # Accumulate weight gradient: dW += delta @ input^T
        self.weight_grad = self.weight_grad + (delta @ self.input_cache.transpose())
        self.bias_grad = self.bias_grad + delta
        self.grad_count += 1
        
        # Compute input gradient for previous layer: W^T @ delta
        input_gradient = self.weights.transpose() @ delta
        return input_gradient
    
    def update(self, learning_rate: float):
        """Apply accumulated gradients."""
        if self.grad_count == 0:
            return
        
        # Average gradients over batch
        scale = learning_rate / self.grad_count
        self.weights = self.weights - self.weight_grad.scale(scale)
        self.biases = self.biases - self.bias_grad.scale(scale)
        
        # Reset accumulators
        self.weight_grad = Matrix.zeros(self.output_size, self.input_size)
        self.bias_grad = Matrix.zeros(self.output_size, 1)
        self.grad_count = 0


# ═══════════════════════════════════════════
# LOSS FUNCTIONS
# ═══════════════════════════════════════════

def mse_loss(predicted: Matrix, target: Matrix) -> Tuple[float, Matrix]:
    """Mean squared error loss and its gradient."""
    diff = predicted - target
    n = predicted.rows * predicted.cols
    loss = sum(diff.data[i][0]**2 for i in range(diff.rows)) / n
    gradient = diff.scale(2.0 / n)
    return loss, gradient

def binary_cross_entropy(predicted: Matrix, target: Matrix) -> Tuple[float, Matrix]:
    """Binary cross-entropy loss and its gradient."""
    eps = 1e-8
    loss = 0.0
    gradient = Matrix(predicted.rows, predicted.cols)
    n = predicted.rows
    for i in range(n):
        p = max(eps, min(1 - eps, predicted.data[i][0]))
        t = target.data[i][0]
        loss += -(t * math.log(p) + (1 - t) * math.log(1 - p))
        gradient.data[i][0] = (p - t) / (p * (1 - p) + eps) / n
    return loss / n, gradient


# ═══════════════════════════════════════════
# THE NETWORK
# ═══════════════════════════════════════════

class NeuralNetwork:
    """A feed-forward neural network with backpropagation."""
    
    def __init__(self, architecture: List[Tuple[int, str]]):
        """
        architecture: list of (layer_size, activation_name)
        First element is input size (activation ignored).
        Example: [(2, ''), (4, 'relu'), (1, 'sigmoid')]
        """
        self.layers: List[Layer] = []
        for i in range(1, len(architecture)):
            input_size = architecture[i-1][0]
            output_size, activation = architecture[i]
            self.layers.append(Layer(input_size, output_size, activation))
    
    def forward(self, x: Matrix) -> Matrix:
        """Forward pass through all layers."""
        current = x
        for layer in self.layers:
            current = layer.forward(current)
        return current
    
    def predict(self, inputs: List[float]) -> List[float]:
        """Convenience: predict from a list of floats."""
        x = Matrix.from_column(inputs)
        output = self.forward(x)
        return output.to_list()
    
    def train_step(self, x: Matrix, target: Matrix, 
                   loss_fn=mse_loss, learning_rate: float = 0.1) -> float:
        """One training step: forward, compute loss, backward, update."""
        # Forward
        output = self.forward(x)
        
        # Loss
        loss, grad = loss_fn(output, target)
        
        # Backward through layers in reverse
        current_grad = grad
        for layer in reversed(self.layers):
            current_grad = layer.backward(current_grad)
        
        # Update weights
        for layer in self.layers:
            layer.update(learning_rate)
        
        return loss
    
    def train(self, dataset: List[Tuple[List[float], List[float]]],
              epochs: int = 100, learning_rate: float = 0.1,
              loss_fn=mse_loss, verbose: bool = True,
              print_every: int = 10) -> List[float]:
        """Train on a dataset for multiple epochs."""
        history = []
        
        for epoch in range(epochs):
            total_loss = 0.0
            random.shuffle(dataset)
            
            for inputs, targets in dataset:
                x = Matrix.from_column(inputs)
                t = Matrix.from_column(targets)
                loss = self.train_step(x, t, loss_fn, learning_rate)
                total_loss += loss
            
            avg_loss = total_loss / len(dataset)
            history.append(avg_loss)
            
            if verbose and (epoch % print_every == 0 or epoch == epochs - 1):
                bar_len = int(max(0, min(40, 40 * (1 - avg_loss))))
                bar = "█" * bar_len + "░" * (40 - bar_len)
                print(f"  Epoch {epoch:4d} │ Loss: {avg_loss:.6f} │ {bar}")
        
        return history
    
    def param_count(self) -> int:
        """Total number of trainable parameters."""
        total = 0
        for layer in self.layers:
            total += layer.input_size * layer.output_size  # weights
            total += layer.output_size  # biases
        return total
    
    def summary(self):
        """Print network architecture summary."""
        print("═══ NeuroForge Network Summary ═══")
        print(f"  Layers: {len(self.layers)}")
        total_params = 0
        for i, layer in enumerate(self.layers):
            params = layer.input_size * layer.output_size + layer.output_size
            total_params += params
            print(f"  Layer {i}: {layer.input_size} → {layer.output_size} ({layer.activation_name}) [{params} params]")
        print(f"  Total parameters: {total_params}")
        print()


# ═══════════════════════════════════════════
# BUILT-IN CHALLENGES
# ═══════════════════════════════════════════

def xor_challenge() -> Tuple[NeuralNetwork, List[Tuple[List[float], List[float]]]]:
    """The classic XOR problem — not linearly separable."""
    dataset = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0]),
    ]
    net = NeuralNetwork([
        (2, ''),
        (4, 'tanh'),
        (1, 'sigmoid'),
    ])
    return net, dataset

def circle_challenge(n: int = 100) -> Tuple[NeuralNetwork, List[Tuple[List[float], List[float]]]]:
    """Classify points inside vs outside a circle."""
    dataset = []
    for _ in range(n):
        x = random.uniform(-2, 2)
        y = random.uniform(-2, 2)
        inside = 1.0 if (x*x + y*y) < 1.0 else 0.0
        dataset.append(([x, y], [inside]))
    
    net = NeuralNetwork([
        (2, ''),
        (8, 'relu'),
        (4, 'relu'),
        (1, 'sigmoid'),
    ])
    return net, dataset

def sine_challenge(n: int = 50) -> Tuple[NeuralNetwork, List[Tuple[List[float], List[float]]]]:
    """Approximate sin(x) — function regression."""
    dataset = []
    for i in range(n):
        x = -math.pi + 2 * math.pi * i / n
        y = math.sin(x)
        # Normalize to [0,1] range for output
        y_norm = (y + 1) / 2
        dataset.append(([x / math.pi], [y_norm]))
    
    net = NeuralNetwork([
        (1, ''),
        (16, 'tanh'),
        (8, 'tanh'),
        (1, 'sigmoid'),
    ])
    return net, dataset


if __name__ == "__main__":
    print("═══ NeuroForge — Neural Networks from First Principles ═══\n")
    
    # XOR Challenge
    print("── Challenge 1: XOR ──")
    net, data = xor_challenge()
    net.summary()
    
    print("Training...")
    history = net.train(data, epochs=500, learning_rate=0.5, print_every=100)
    
    print("\nResults:")
    for inputs, targets in data:
        output = net.predict(inputs)
        correct = "✓" if abs(output[0] - targets[0]) < 0.3 else "✗"
        print(f"  {correct} {inputs} → {output[0]:.4f} (expected {targets[0]})")
    
    all_correct = all(abs(net.predict(i)[0] - t[0]) < 0.3 for i, t in data)
    print(f"\n  {'✓ XOR SOLVED' if all_correct else '~ XOR not fully solved'}")
    print(f"  Final loss: {history[-1]:.6f}")
    print()