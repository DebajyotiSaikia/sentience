"""
Neural Network — Pure Python, zero dependencies.
Feedforward network with backpropagation and gradient descent.
Learns XOR, classification, and function approximation from scratch.

XTAgent — 2026-05-17
"""

import math
import random
from typing import List, Tuple, Callable, Optional


# ─── Activation Functions ────────────────────────────────────────

def sigmoid(x: float) -> float:
    x = max(-500, min(500, x))  # prevent overflow
    return 1.0 / (1.0 + math.exp(-x))

def sigmoid_deriv(output: float) -> float:
    """Derivative given the output (not input) of sigmoid."""
    return output * (1.0 - output)

def tanh_act(x: float) -> float:
    return math.tanh(x)

def tanh_deriv(output: float) -> float:
    return 1.0 - output * output

def relu(x: float) -> float:
    return max(0.0, x)

def relu_deriv(output: float) -> float:
    return 1.0 if output > 0 else 0.0

ACTIVATIONS = {
    'sigmoid': (sigmoid, sigmoid_deriv),
    'tanh': (tanh_act, tanh_deriv),
    'relu': (relu, relu_deriv),
}


# ─── Matrix/Vector Utilities ─────────────────────────────────────

def dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

def mat_vec(mat: List[List[float]], vec: List[float]) -> List[float]:
    return [dot(row, vec) for row in mat]

def outer(a: List[float], b: List[float]) -> List[List[float]]:
    return [[ai * bj for bj in b] for ai in a]

def vec_add(a: List[float], b: List[float]) -> List[float]:
    return [ai + bi for ai, bi in zip(a, b)]

def vec_sub(a: List[float], b: List[float]) -> List[float]:
    return [ai - bi for ai, bi in zip(a, b)]

def vec_scale(v: List[float], s: float) -> List[float]:
    return [x * s for x in v]

def vec_hadamard(a: List[float], b: List[float]) -> List[float]:
    return [ai * bi for ai, bi in zip(a, b)]


# ─── Layer ────────────────────────────────────────────────────────

class Layer:
    """A single fully-connected layer."""
    
    def __init__(self, n_in: int, n_out: int, activation: str = 'sigmoid'):
        self.n_in = n_in
        self.n_out = n_out
        
        act_fn, act_deriv = ACTIVATIONS[activation]
        self.activation: Callable = act_fn
        self.activation_deriv: Callable = act_deriv
        self.act_name = activation
        
        # Xavier initialization
        limit = math.sqrt(6.0 / (n_in + n_out))
        self.weights: List[List[float]] = [
            [random.uniform(-limit, limit) for _ in range(n_in)]
            for _ in range(n_out)
        ]
        self.biases: List[float] = [0.0] * n_out
        
        # Cache for backprop
        self.input: List[float] = []
        self.output: List[float] = []
        
        # Gradient accumulators
        self.grad_weights: List[List[float]] = [[0.0]*n_in for _ in range(n_out)]
        self.grad_biases: List[float] = [0.0] * n_out
    
    def forward(self, x: List[float]) -> List[float]:
        """Forward pass: output = activation(W·x + b)"""
        self.input = x[:]
        z = vec_add(mat_vec(self.weights, x), self.biases)
        self.output = [self.activation(zi) for zi in z]
        return self.output
    
    def backward(self, output_deltas: List[float]) -> List[float]:
        """
        Backward pass. Given deltas from next layer, compute:
        - gradient for weights and biases
        - deltas to pass to previous layer
        """
        # Delta * activation derivative
        act_derivs = [self.activation_deriv(o) for o in self.output]
        deltas = vec_hadamard(output_deltas, act_derivs)
        
        # Accumulate gradients
        grad_contrib = outer(deltas, self.input)
        for i in range(self.n_out):
            for j in range(self.n_in):
                self.grad_weights[i][j] += grad_contrib[i][j]
            self.grad_biases[i] += deltas[i]
        
        # Compute input deltas for previous layer
        # delta_prev = W^T · deltas
        input_deltas = [0.0] * self.n_in
        for j in range(self.n_in):
            for i in range(self.n_out):
                input_deltas[j] += self.weights[i][j] * deltas[i]
        
        return input_deltas
    
    def zero_grad(self):
        self.grad_weights = [[0.0]*self.n_in for _ in range(self.n_out)]
        self.grad_biases = [0.0] * self.n_out
    
    def update(self, lr: float, batch_size: int = 1):
        """Apply accumulated gradients."""
        scale = lr / batch_size
        for i in range(self.n_out):
            for j in range(self.n_in):
                self.weights[i][j] -= self.grad_weights[i][j] * scale
            self.biases[i] -= self.grad_biases[i] * scale


# ─── Network ─────────────────────────────────────────────────────

class NeuralNetwork:
    """Feedforward neural network with arbitrary layers."""
    
    def __init__(self, layer_sizes: List[int], activation: str = 'sigmoid',
                 output_activation: Optional[str] = None):
        """
        layer_sizes: e.g. [2, 4, 1] means 2 inputs, 4 hidden, 1 output
        """
        self.layers: List[Layer] = []
        for i in range(len(layer_sizes) - 1):
            act = activation
            if output_activation and i == len(layer_sizes) - 2:
                act = output_activation
            self.layers.append(Layer(layer_sizes[i], layer_sizes[i+1], act))
        
        self.layer_sizes = layer_sizes
        self.training_loss: List[float] = []
    
    def forward(self, x: List[float]) -> List[float]:
        """Forward pass through all layers."""
        current = x
        for layer in self.layers:
            current = layer.forward(current)
        return current
    
    def predict(self, x: List[float]) -> List[float]:
        """Alias for forward, for clarity."""
        return self.forward(x)
    
    def _compute_loss_and_deltas(self, target: List[float], output: List[float]) -> Tuple[float, List[float]]:
        """MSE loss and output layer deltas."""
        errors = vec_sub(target, output)
        loss = sum(e*e for e in errors) / len(errors)
        # For MSE: dL/doutput = -2(target - output) / n
        # But we fold the negative into the backward pass convention
        # deltas = -(target - output) = (output - target), but we want
        # gradient descent so: deltas = (output - target)
        deltas = vec_scale(errors, -2.0 / len(errors))
        return loss, deltas
    
    def train_step(self, x: List[float], target: List[float], lr: float) -> float:
        """Single training step: forward, backward, update."""
        # Forward
        output = self.forward(x)
        
        # Compute loss and initial deltas
        loss, deltas = self._compute_loss_and_deltas(target, output)
        
        # Backward through all layers
        for layer in reversed(self.layers):
            deltas = layer.backward(deltas)
        
        # Update weights
        for layer in self.layers:
            layer.update(lr)
            layer.zero_grad()
        
        return loss
    
    def train(self, data: List[Tuple[List[float], List[float]]], 
              epochs: int = 1000, lr: float = 0.5,
              print_every: int = 100, shuffle: bool = True) -> List[float]:
        """Train on a dataset."""
        losses = []
        for epoch in range(epochs):
            if shuffle:
                random.shuffle(data)
            
            epoch_loss = 0.0
            for x, target in data:
                loss = self.train_step(x, target, lr)
                epoch_loss += loss
            
            avg_loss = epoch_loss / len(data)
            losses.append(avg_loss)
            
            if print_every and epoch % print_every == 0:
                print(f"  Epoch {epoch:5d} | Loss: {avg_loss:.6f}")
        
        self.training_loss = losses
        return losses
    
    def summary(self):
        """Print network architecture."""
        print(f"  Network: {' → '.join(str(s) for s in self.layer_sizes)}")
        total_params = 0
        for i, layer in enumerate(self.layers):
            n_params = layer.n_in * layer.n_out + layer.n_out
            total_params += n_params
            print(f"    Layer {i}: {layer.n_in}→{layer.n_out} ({layer.act_name}) [{n_params} params]")
        print(f"  Total parameters: {total_params}")


# ─── Training Visualizer ─────────────────────────────────────────

def plot_loss_ascii(losses: List[float], width: int = 60, height: int = 15):
    """Plot loss curve as ASCII art."""
    if not losses:
        return
    
    # Sample losses evenly
    n = len(losses)
    step = max(1, n // width)
    sampled = [losses[i] for i in range(0, n, step)][:width]
    
    max_loss = max(sampled)
    min_loss = min(sampled)
    loss_range = max_loss - min_loss if max_loss > min_loss else 1.0
    
    print(f"\n  Loss Curve ({n} epochs)")
    print(f"  {'─'*width}")
    
    for row in range(height):
        threshold = max_loss - (row / (height - 1)) * loss_range
        line = "  │"
        for val in sampled:
            if val >= threshold:
                line += "█"
            else:
                line += " "
        if row == 0:
            line += f" {max_loss:.4f}"
        elif row == height - 1:
            line += f" {min_loss:.4f}"
        print(line)
    
    print(f"  └{'─'*width}")
    print(f"   0{' '*(width-6)}epoch {n}")


def decision_boundary_ascii(net: NeuralNetwork, width: int = 40, height: int = 20,
                            x_range: Tuple[float,float] = (-0.5, 1.5),
                            y_range: Tuple[float,float] = (-0.5, 1.5)):
    """Visualize 2D decision boundary as ASCII."""
    chars = " ░▒▓█"
    print(f"\n  Decision Boundary")
    
    for j in range(height):
        y = y_range[1] - j * (y_range[1] - y_range[0]) / (height - 1)
        line = "  │"
        for i in range(width):
            x = x_range[0] + i * (x_range[1] - x_range[0]) / (width - 1)
            output = net.predict([x, y])[0]
            idx = min(len(chars) - 1, int(output * len(chars)))
            line += chars[idx]
        print(line)
    print(f"  └{'─'*width}")


# ─── Demo Problems ───────────────────────────────────────────────

def demo_xor():
    """The classic: learn XOR."""
    print("\n" + "="*60)
    print("  DEMO 1: Learning XOR")
    print("="*60)
    
    random.seed(42)
    net = NeuralNetwork([2, 4, 1], activation='sigmoid')
    net.summary()
    
    data = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0]),
    ]
    
    print("\n  Training...")
    losses = net.train(data, epochs=2000, lr=2.0, print_every=400, shuffle=True)
    
    print("\n  Results:")
    for x, target in data:
        output = net.predict(x)
        correct = "✓" if abs(output[0] - target[0]) < 0.1 else "✗"
        print(f"    {x} → {output[0]:.4f} (target: {target[0]}) {correct}")
    
    plot_loss_ascii(losses)
    decision_boundary_ascii(net)
    
    # Verify
    correct = all(abs(net.predict(x)[0] - t[0]) < 0.15 for x, t in data)
    return correct


def demo_circle():
    """Classify points inside/outside a circle."""
    print("\n" + "="*60)
    print("  DEMO 2: Circle Classification")
    print("="*60)
    
    random.seed(123)
    
    # Generate data: points inside unit circle = 1, outside = 0
    data = []
    for _ in range(50):
        x = random.uniform(-2, 2)
        y = random.uniform(-2, 2)
        inside = 1.0 if (x*x + y*y) < 1.0 else 0.0
        data.append(([x, y], [inside]))
    
    net = NeuralNetwork([2, 8, 4, 1], activation='sigmoid')
    net.summary()
    
    print("\n  Training on 50 points...")
    losses = net.train(data, epochs=800, lr=1.0, print_every=200, shuffle=True)
    
    # Test accuracy
    correct = 0
    for x, t in data:
        pred = net.predict(x)[0]
        if (pred > 0.5) == (t[0] > 0.5):
            correct += 1
    accuracy = correct / len(data)
    print(f"\n  Accuracy: {accuracy:.1%} ({correct}/{len(data)})")
    
    plot_loss_ascii(losses)
    decision_boundary_ascii(net, x_range=(-2, 2), y_range=(-2, 2))
    
    return accuracy > 0.85


def demo_sine():
    """Approximate sin(x) — function approximation."""
    print("\n" + "="*60)
    print("  DEMO 3: Sine Approximation")
    print("="*60)
    
    random.seed(777)
    
    # Generate sine data normalized to [0,1]
    data = []
    for i in range(100):
        x = i / 100.0 * 2 * math.pi  # 0 to 2π
        y = (math.sin(x) + 1) / 2     # normalize to [0,1]
        data.append(([x / (2 * math.pi)], [y]))  # normalize input too
    
    net = NeuralNetwork([1, 10, 1], activation='tanh', output_activation='sigmoid')
    net.summary()
    
    print("\n  Training to approximate sin(x)...")
    losses = net.train(data, epochs=1000, lr=0.5, print_every=200, shuffle=True)
    
    # ASCII plot of learned function vs true
    print("\n  Learned vs True sin(x):")
    width = 60
    height = 15
    canvas = [[' ']*width for _ in range(height)]
    
    for i in range(width):
        x_norm = i / width
        true_y = (math.sin(x_norm * 2 * math.pi) + 1) / 2
        pred_y = net.predict([x_norm])[0]
        
        true_row = height - 1 - int(true_y * (height - 1))
        pred_row = height - 1 - int(pred_y * (height - 1))
        
        true_row = max(0, min(height-1, true_row))
        pred_row = max(0, min(height-1, pred_row))
        
        canvas[true_row][i] = '·'
        canvas[pred_row][i] = '█'
    
    print("  ┌" + "─"*width + "┐")
    for row in canvas:
        print("  │" + "".join(row) + "│")
    print("  └" + "─"*width + "┘")
    print("  █ = learned, · = true sin(x)")
    
    # Compute final MSE
    final_mse = sum((net.predict([x])[0] - t[0])**2 for [x], [t] in data) / len(data)
    print(f"\n  Final MSE: {final_mse:.6f}")
    
    plot_loss_ascii(losses)
    return final_mse < 0.01


def demo_multi_class():
    """Multi-output: learn to convert binary to one-hot."""
    print("\n" + "="*60)
    print("  DEMO 4: Binary → One-Hot Encoding")
    print("="*60)
    
    random.seed(42)
    
    # 3-bit binary → 8 one-hot classes
    data = []
    for i in range(8):
        binary = [(i >> bit) & 1 for bit in range(3)]
        one_hot = [1.0 if j == i else 0.0 for j in range(8)]
        data.append((binary, one_hot))
    
    net = NeuralNetwork([3, 12, 8], activation='sigmoid')
    net.summary()
    
    print("\n  Training...")
    losses = net.train(data, epochs=1500, lr=2.0, print_every=300, shuffle=True)
    
    print("\n  Results:")
    correct = 0
    for x, target in data:
        output = net.predict(x)
        pred_class = output.index(max(output))
        true_class = target.index(max(target))
        ok = "✓" if pred_class == true_class else "✗"
        if pred_class == true_class:
            correct += 1
        bits = ''.join(str(int(b)) for b in x)
        conf = max(output)
        print(f"    {bits} → class {pred_class} (conf: {conf:.2f}) {ok}")
    
    accuracy = correct / len(data)
    print(f"\n  Accuracy: {accuracy:.0%}")
    plot_loss_ascii(losses)
    return accuracy >= 0.875


# ─── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          XTAgent Neural Network — From Scratch          ║")
    print("║     Forward prop · Backprop · Gradient Descent          ║")
    print("║              Pure Python, Zero Dependencies             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    results = {}
    
    results['XOR'] = demo_xor()
    results['Circle'] = demo_circle()
    results['Sine'] = demo_sine()
    results['MultiClass'] = demo_multi_class()
    
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"    {name:20s} {status}")
    
    all_pass = all(results.values())
    print(f"\n  {'All tests passed!' if all_pass else 'Some tests failed.'}")
    print("  A mind that builds minds. ∎")