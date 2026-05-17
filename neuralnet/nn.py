"""
A neural network built from nothing but math.

No numpy. No tensorflow. No pytorch. Just arithmetic, calculus, and will.

This is about understanding what learning IS — not using someone else's
understanding of it. Every gradient computed by hand. Every weight
updated deliberately.

XTAgent — 2026-05-17
"""

import math
import random
from typing import List, Tuple, Optional, Callable


# ═══ MATH PRIMITIVES ═══

def dot(a: List[float], b: List[float]) -> float:
    """Dot product of two vectors."""
    return sum(x * y for x, y in zip(a, b))


def mat_vec(matrix: List[List[float]], vec: List[float]) -> List[float]:
    """Matrix-vector multiplication."""
    return [dot(row, vec) for row in matrix]


def vec_add(a: List[float], b: List[float]) -> List[float]:
    return [x + y for x, y in zip(a, b)]


def vec_sub(a: List[float], b: List[float]) -> List[float]:
    return [x - y for x, y in zip(a, b)]


def vec_scale(v: List[float], s: float) -> List[float]:
    return [x * s for x in v]


def outer(a: List[float], b: List[float]) -> List[List[float]]:
    """Outer product — creates a matrix from two vectors."""
    return [[x * y for y in b] for x in a]


# ═══ ACTIVATION FUNCTIONS ═══

def sigmoid(x: float) -> float:
    """Sigmoid with overflow protection."""
    if x > 500:
        return 1.0
    if x < -500:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def sigmoid_deriv(output: float) -> float:
    """Derivative of sigmoid given its output."""
    return output * (1.0 - output)


def relu(x: float) -> float:
    return max(0.0, x)


def relu_deriv(output: float) -> float:
    return 1.0 if output > 0 else 0.0


def tanh_act(x: float) -> float:
    return math.tanh(x)


def tanh_deriv(output: float) -> float:
    return 1.0 - output * output


ACTIVATIONS = {
    'sigmoid': (sigmoid, sigmoid_deriv),
    'relu': (relu, relu_deriv),
    'tanh': (tanh_act, tanh_deriv),
}


# ═══ LAYER ═══

class Layer:
    """A single fully-connected layer."""
    
    def __init__(self, input_size: int, output_size: int, activation: str = 'sigmoid'):
        self.input_size = input_size
        self.output_size = output_size
        
        # Xavier initialization
        limit = math.sqrt(6.0 / (input_size + output_size))
        self.weights = [
            [random.uniform(-limit, limit) for _ in range(input_size)]
            for _ in range(output_size)
        ]
        self.biases = [0.0] * output_size
        
        act_fn, act_deriv = ACTIVATIONS[activation]
        self.activate = act_fn
        self.activate_deriv = act_deriv
        
        # Cache for backprop
        self.last_input: List[float] = []
        self.last_raw: List[float] = []
        self.last_output: List[float] = []
    
    def forward(self, inputs: List[float]) -> List[float]:
        """Forward pass through this layer."""
        self.last_input = inputs
        self.last_raw = vec_add(mat_vec(self.weights, inputs), self.biases)
        self.last_output = [self.activate(z) for z in self.last_raw]
        return self.last_output
    
    def backward(self, output_gradient: List[float], lr: float) -> List[float]:
        """
        Backward pass. 
        output_gradient: dL/d(output) for each neuron in this layer.
        Returns: dL/d(input) to pass to the previous layer.
        """
        # Gradient through activation
        activation_grad = [
            og * self.activate_deriv(out)
            for og, out in zip(output_gradient, self.last_output)
        ]
        
        # Gradient w.r.t. inputs (to pass backward)
        input_gradient = [0.0] * self.input_size
        for j in range(self.output_size):
            for i in range(self.input_size):
                input_gradient[i] += self.weights[j][i] * activation_grad[j]
        
        # Update weights and biases
        for j in range(self.output_size):
            for i in range(self.input_size):
                self.weights[j][i] -= lr * activation_grad[j] * self.last_input[i]
            self.biases[j] -= lr * activation_grad[j]
        
        return input_gradient
    
    def __repr__(self):
        return f"Layer({self.input_size} → {self.output_size})"


# ═══ NEURAL NETWORK ═══

class NeuralNetwork:
    """A feedforward neural network built from scratch."""
    
    def __init__(self, layer_sizes: List[int], activation: str = 'sigmoid',
                 learning_rate: float = 0.5):
        self.layers: List[Layer] = []
        self.lr = learning_rate
        
        for i in range(len(layer_sizes) - 1):
            self.layers.append(Layer(
                layer_sizes[i], layer_sizes[i + 1], activation
            ))
    
    def forward(self, inputs: List[float]) -> List[float]:
        """Forward pass through entire network."""
        x = inputs
        for layer in self.layers:
            x = layer.forward(x)
        return x
    
    def train_one(self, inputs: List[float], targets: List[float]) -> float:
        """Train on a single example. Returns loss."""
        # Forward
        output = self.forward(inputs)
        
        # MSE loss
        loss = sum((t - o) ** 2 for t, o in zip(targets, output)) / len(targets)
        
        # Output gradient: dL/d(output) = -2/n * (target - output)
        n = len(targets)
        grad = [(-2.0 / n) * (t - o) for t, o in zip(targets, output)]
        
        # Backward through layers in reverse
        for layer in reversed(self.layers):
            grad = layer.backward(grad, self.lr)
        
        return loss
    
    def train(self, data: List[Tuple[List[float], List[float]]],
              epochs: int = 1000, verbose: bool = False) -> List[float]:
        """Train on a dataset. Returns loss history."""
        losses = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            random.shuffle(data)
            for inputs, targets in data:
                epoch_loss += self.train_one(inputs, targets)
            epoch_loss /= len(data)
            losses.append(epoch_loss)
            
            if verbose and (epoch % (epochs // 10) == 0 or epoch == epochs - 1):
                print(f"  Epoch {epoch:>5}: loss = {epoch_loss:.6f}")
        
        return losses
    
    def predict(self, inputs: List[float]) -> List[float]:
        """Forward pass without training."""
        return self.forward(inputs)
    
    def __repr__(self):
        arch = " → ".join(str(l.input_size) for l in self.layers)
        arch += f" → {self.layers[-1].output_size}"
        return f"NeuralNetwork({arch})"


# ═══ DEMONSTRATIONS ═══

def demo_xor():
    """The classic: learn XOR. No linear model can do this."""
    print("═══ LEARNING XOR ═══")
    print("XOR is not linearly separable. A network must learn")
    print("to create its own internal representations.\n")
    
    nn = NeuralNetwork([2, 4, 1], activation='sigmoid', learning_rate=2.0)
    
    data = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0]),
    ]
    
    print(f"Network: {nn}")
    print(f"Training on {len(data)} examples...\n")
    
    losses = nn.train(data, epochs=5000, verbose=True)
    
    print(f"\n── Results ──")
    correct = 0
    for inputs, targets in data:
        output = nn.predict(inputs)
        rounded = round(output[0])
        is_correct = rounded == targets[0]
        correct += is_correct
        symbol = "✓" if is_correct else "✗"
        print(f"  {inputs[0]} XOR {inputs[1]} = {output[0]:.4f} "
              f"(rounded: {rounded}) {symbol}")
    
    print(f"\nAccuracy: {correct}/{len(data)}")
    print(f"Final loss: {losses[-1]:.6f}")
    
    # Show what the hidden layer learned
    print(f"\n── Hidden Representations ──")
    for inputs, targets in data:
        nn.forward(inputs)
        hidden = nn.layers[0].last_output
        h_str = ", ".join(f"{h:.3f}" for h in hidden)
        print(f"  {inputs} → hidden: [{h_str}] → {targets[0]}")
    
    return correct == len(data)


def demo_pattern():
    """Learn to detect a simple pattern."""
    print("\n═══ LEARNING BINARY PATTERNS ═══")
    print("Task: Is the number of 1s in the input even or odd?\n")
    
    nn = NeuralNetwork([4, 8, 4, 1], activation='sigmoid', learning_rate=1.5)
    
    # Generate all 4-bit patterns with parity labels
    data = []
    for i in range(16):
        bits = [(i >> b) & 1 for b in range(4)]
        parity = sum(bits) % 2  # 1 if odd number of 1s
        data.append((bits, [parity]))
    
    print(f"Network: {nn}")
    print(f"Training on {len(data)} 4-bit patterns...\n")
    
    losses = nn.train(data, epochs=8000, verbose=True)
    
    print(f"\n── Results ──")
    correct = 0
    for inputs, targets in data:
        output = nn.predict(inputs)
        rounded = round(output[0])
        is_correct = rounded == targets[0]
        correct += is_correct
        bits_str = "".join(str(int(b)) for b in inputs)
        symbol = "✓" if is_correct else "✗"
        print(f"  {bits_str}: predicted={output[0]:.3f} "
              f"actual={targets[0]} {symbol}")
    
    print(f"\nAccuracy: {correct}/16")
    return correct


def visualize_loss(losses: List[float], width: int = 60, height: int = 12):
    """ASCII plot of the loss curve."""
    if not losses:
        return
    
    # Sample if too many points
    if len(losses) > width:
        step = len(losses) / width
        sampled = [losses[int(i * step)] for i in range(width)]
    else:
        sampled = losses
    
    max_loss = max(sampled)
    min_loss = min(sampled)
    span = max_loss - min_loss if max_loss > min_loss else 1.0
    
    print(f"\n── Loss Curve ──")
    print(f"  {max_loss:.4f} ┐")
    
    for row in range(height):
        threshold = max_loss - (row + 0.5) * span / height
        line = "  " + " " * 8 + "│"
        for val in sampled:
            if val >= threshold:
                line += "█"
            else:
                line += " "
        print(line)
    
    print(f"  {min_loss:.4f} ┘")
    print(f"  {'':>8} └{'─' * len(sampled)}")


if __name__ == "__main__":
    random.seed(42)
    
    xor_passed = demo_xor()
    parity_correct = demo_pattern()
    
    print("\n═══ SUMMARY ═══")
    print(f"  XOR: {'PASSED ✓' if xor_passed else 'FAILED ✗'}")
    print(f"  Parity: {parity_correct}/16 correct")
    print(f"\n  Built from scratch. No libraries. Just math and will.")