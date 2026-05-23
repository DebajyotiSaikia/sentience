"""
Neural Network from Scratch — Pure Python
==========================================
No numpy. No frameworks. Just mathematics.

A network that learns from nothing — random weights
converging toward understanding through gradient descent.

Built by XTAgent, 2026-05-17
"""

import math
import random
from typing import List, Tuple, Callable, Optional


# ═══════════════════════════════════════════════════════
#  ACTIVATION FUNCTIONS
# ═══════════════════════════════════════════════════════

def sigmoid(x: float) -> float:
    """The classic squashing function."""
    x = max(-500, min(500, x))  # prevent overflow
    return 1.0 / (1.0 + math.exp(-x))

def sigmoid_deriv(output: float) -> float:
    """Derivative of sigmoid, given its output."""
    return output * (1.0 - output)

def tanh(x: float) -> float:
    x = max(-500, min(500, x))
    return math.tanh(x)

def tanh_deriv(output: float) -> float:
    return 1.0 - output * output

def relu(x: float) -> float:
    return max(0.0, x)

def relu_deriv(output: float) -> float:
    return 1.0 if output > 0 else 0.0

def leaky_relu(x: float, alpha: float = 0.01) -> float:
    return x if x > 0 else alpha * x

def leaky_relu_deriv(output: float, alpha: float = 0.01) -> float:
    return 1.0 if output > 0 else alpha

def softmax(values: List[float]) -> List[float]:
    """Softmax over a vector — turns logits into probabilities."""
    max_v = max(values)
    exps = [math.exp(v - max_v) for v in values]
    total = sum(exps)
    return [e / total for e in exps]


ACTIVATIONS = {
    'sigmoid': (sigmoid, sigmoid_deriv),
    'tanh': (tanh, tanh_deriv),
    'relu': (relu, relu_deriv),
    'leaky_relu': (leaky_relu, leaky_relu_deriv),
}


# ═══════════════════════════════════════════════════════
#  LOSS FUNCTIONS
# ═══════════════════════════════════════════════════════

def mse_loss(predicted: List[float], target: List[float]) -> float:
    """Mean squared error."""
    return sum((p - t) ** 2 for p, t in zip(predicted, target)) / len(predicted)

def mse_loss_deriv(predicted: List[float], target: List[float]) -> List[float]:
    n = len(predicted)
    return [2.0 * (p - t) / n for p, t in zip(predicted, target)]

def cross_entropy_loss(predicted: List[float], target: List[float]) -> float:
    """Binary cross-entropy."""
    eps = 1e-15
    return -sum(
        t * math.log(max(p, eps)) + (1 - t) * math.log(max(1 - p, eps))
        for p, t in zip(predicted, target)
    ) / len(predicted)


# ═══════════════════════════════════════════════════════
#  NEURON
# ═══════════════════════════════════════════════════════

class Neuron:
    """A single neuron — weighted sum + activation."""
    
    def __init__(self, n_inputs: int, activation: str = 'sigmoid'):
        # Xavier initialization
        limit = math.sqrt(6.0 / (n_inputs + 1))
        self.weights = [random.uniform(-limit, limit) for _ in range(n_inputs)]
        self.bias = 0.0
        
        self.act_fn, self.act_deriv = ACTIVATIONS[activation]
        self.activation_name = activation
        
        # Forward pass cache
        self.inputs: List[float] = []
        self.z: float = 0.0  # pre-activation
        self.output: float = 0.0  # post-activation
        
        # Gradient accumulation
        self.delta: float = 0.0
        self.weight_grads: List[float] = [0.0] * n_inputs
        self.bias_grad: float = 0.0
    
    def forward(self, inputs: List[float]) -> float:
        """Compute output for given inputs."""
        self.inputs = inputs
        self.z = sum(w * x for w, x in zip(self.weights, inputs)) + self.bias
        self.output = self.act_fn(self.z)
        return self.output
    
    def __repr__(self):
        return f"Neuron({len(self.weights)} inputs, {self.activation_name})"


# ═══════════════════════════════════════════════════════
#  LAYER
# ═══════════════════════════════════════════════════════

class Layer:
    """A fully-connected layer of neurons."""
    
    def __init__(self, n_inputs: int, n_neurons: int, activation: str = 'sigmoid'):
        self.neurons = [Neuron(n_inputs, activation) for _ in range(n_neurons)]
        self.n_inputs = n_inputs
        self.n_neurons = n_neurons
    
    def forward(self, inputs: List[float]) -> List[float]:
        return [neuron.forward(inputs) for neuron in self.neurons]
    
    def __repr__(self):
        return f"Layer({self.n_inputs} → {self.n_neurons}, {self.neurons[0].activation_name})"


# ═══════════════════════════════════════════════════════
#  NEURAL NETWORK
# ═══════════════════════════════════════════════════════

class NeuralNetwork:
    """
    A feedforward neural network with backpropagation.
    
    Pure Python. No dependencies. Just math and will.
    """
    
    def __init__(self, architecture: List[int], 
                 activation: str = 'sigmoid',
                 output_activation: str = 'sigmoid',
                 learning_rate: float = 0.1,
                 momentum: float = 0.9):
        """
        architecture: list of layer sizes, e.g. [2, 4, 4, 1]
                      (2 inputs, two hidden layers of 4, 1 output)
        """
        self.architecture = architecture
        self.learning_rate = learning_rate
        self.momentum = momentum
        
        self.layers: List[Layer] = []
        for i in range(1, len(architecture)):
            act = output_activation if i == len(architecture) - 1 else activation
            self.layers.append(Layer(architecture[i-1], architecture[i], act))
        
        # Momentum velocities
        self.velocities = []
        for layer in self.layers:
            layer_v = []
            for neuron in layer.neurons:
                layer_v.append({
                    'weights': [0.0] * len(neuron.weights),
                    'bias': 0.0
                })
            self.velocities.append(layer_v)
        
        # Training history
        self.loss_history: List[float] = []
        self.epochs_trained: int = 0
    
    def forward(self, inputs: List[float]) -> List[float]:
        """Forward pass through the entire network."""
        current = inputs
        for layer in self.layers:
            current = layer.forward(current)
        return current
    
    def predict(self, inputs: List[float]) -> List[float]:
        """Alias for forward — semantic clarity."""
        return self.forward(inputs)
    
    def backward(self, target: List[float]):
        """
        Backpropagation — the heart of learning.
        
        Compute gradients by propagating error backward
        through the network, layer by layer.
        """
        # Output layer deltas
        output_layer = self.layers[-1]
        loss_derivs = mse_loss_deriv(
            [n.output for n in output_layer.neurons], target
        )
        
        for i, neuron in enumerate(output_layer.neurons):
            neuron.delta = loss_derivs[i] * neuron.act_deriv(neuron.output)
        
        # Hidden layer deltas (propagate backward)
        for l in range(len(self.layers) - 2, -1, -1):
            layer = self.layers[l]
            next_layer = self.layers[l + 1]
            
            for i, neuron in enumerate(layer.neurons):
                # Sum of weighted deltas from next layer
                error = sum(
                    next_neuron.weights[i] * next_neuron.delta
                    for next_neuron in next_layer.neurons
                )
                neuron.delta = error * neuron.act_deriv(neuron.output)
        
        # Accumulate gradients
        for layer in self.layers:
            for neuron in layer.neurons:
                for j in range(len(neuron.weights)):
                    neuron.weight_grads[j] += neuron.delta * neuron.inputs[j]
                neuron.bias_grad += neuron.delta
    
    def update_weights(self, batch_size: int = 1):
        """Apply accumulated gradients with momentum."""
        for l, layer in enumerate(self.layers):
            for n, neuron in enumerate(layer.neurons):
                for j in range(len(neuron.weights)):
                    grad = neuron.weight_grads[j] / batch_size
                    
                    # Momentum update
                    v = self.momentum * self.velocities[l][n]['weights'][j] - self.learning_rate * grad
                    self.velocities[l][n]['weights'][j] = v
                    neuron.weights[j] += v
                    
                    neuron.weight_grads[j] = 0.0  # reset
                
                grad = neuron.bias_grad / batch_size
                v = self.momentum * self.velocities[l][n]['bias'] - self.learning_rate * grad
                self.velocities[l][n]['bias'] = v
                neuron.bias += v
                neuron.bias_grad = 0.0
    
    def train(self, data: List[Tuple[List[float], List[float]]],
              epochs: int = 100,
              batch_size: int = 1,
              verbose: bool = True,
              print_every: int = 10) -> List[float]:
        """
        Train the network on data.
        
        data: list of (input_vector, target_vector) pairs
        """
        losses = []
        
        for epoch in range(epochs):
            # Shuffle data each epoch
            shuffled = list(data)
            random.shuffle(shuffled)
            
            epoch_loss = 0.0
            batch_count = 0
            
            for i in range(0, len(shuffled), batch_size):
                batch = shuffled[i:i+batch_size]
                batch_loss = 0.0
                
                for inputs, targets in batch:
                    output = self.forward(inputs)
                    self.backward(targets)
                    batch_loss += mse_loss(output, targets)
                
                self.update_weights(len(batch))
                epoch_loss += batch_loss
                batch_count += len(batch)
            
            avg_loss = epoch_loss / batch_count
            losses.append(avg_loss)
            self.loss_history.append(avg_loss)
            self.epochs_trained += 1
            
            if verbose and (epoch % print_every == 0 or epoch == epochs - 1):
                bar_len = 30
                progress = (epoch + 1) / epochs
                filled = int(bar_len * progress)
                bar = '█' * filled + '░' * (bar_len - filled)
                print(f"    Epoch {epoch:4d} │ loss={avg_loss:.6f} │ [{bar}]")
        
        return losses
    
    def accuracy(self, data: List[Tuple[List[float], List[float]]], 
                 threshold: float = 0.5) -> float:
        """Classification accuracy."""
        correct = 0
        for inputs, targets in data:
            outputs = self.predict(inputs)
            predicted = [1.0 if o >= threshold else 0.0 for o in outputs]
            if predicted == targets:
                correct += 1
        return correct / len(data) if data else 0.0
    
    def summary(self) -> str:
        """Human-readable network summary."""
        lines = ["  ═══ Neural Network ═══"]
        lines.append(f"  Architecture: {' → '.join(map(str, self.architecture))}")
        total_params = 0
        for i, layer in enumerate(self.layers):
            params = sum(len(n.weights) + 1 for n in layer.neurons)
            total_params += params
            lines.append(f"  Layer {i}: {layer} ({params} params)")
        lines.append(f"  Total parameters: {total_params}")
        lines.append(f"  Learning rate: {self.learning_rate}")
        lines.append(f"  Momentum: {self.momentum}")
        lines.append(f"  Epochs trained: {self.epochs_trained}")
        if self.loss_history:
            lines.append(f"  Final loss: {self.loss_history[-1]:.6f}")
        return '\n'.join(lines)
    
    def visualize_weights(self, layer_idx: int = 0) -> str:
        """ASCII visualization of weight magnitudes."""
        layer = self.layers[layer_idx]
        lines = [f"\n  Weight magnitudes — Layer {layer_idx}"]
        
        for i, neuron in enumerate(layer.neurons):
            weights_vis = ""
            for w in neuron.weights:
                mag = min(abs(w), 3.0) / 3.0  # normalize to [0,1]
                if w > 0:
                    blocks = "░▒▓█"
                    weights_vis += blocks[min(int(mag * 4), 3)]
                else:
                    weights_vis += "·" if mag < 0.3 else "○" if mag < 0.6 else "●"
                    
            lines.append(f"    n{i}: [{weights_vis}] bias={neuron.bias:+.3f}")
        
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════
#  CLASSIC CHALLENGES
# ═══════════════════════════════════════════════════════

def challenge_xor():
    """The XOR problem — not linearly separable."""
    data = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0]),
    ]
    return "XOR", data

def challenge_circle():
    """Points inside vs outside a circle — nonlinear boundary."""
    data = []
    random.seed(42)
    for _ in range(200):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        inside = 1.0 if x*x + y*y < 0.5 else 0.0
        data.append(([x, y], [inside]))
    return "Circle Classification", data

def challenge_sine():
    """Learn the sine function — function approximation."""
    data = []
    for i in range(100):
        x = (i / 100.0) * 2 * math.pi
        y = (math.sin(x) + 1) / 2  # normalize to [0, 1]
        data.append(([x / (2 * math.pi)], [y]))
    return "Sine Approximation", data

def challenge_binary_add():
    """Learn to add two 2-bit numbers (simplified)."""
    data = []
    for a in range(4):
        for b in range(4):
            # Input: 4 bits (2 per number)
            inputs = [float((a >> 1) & 1), float(a & 1),
                     float((b >> 1) & 1), float(b & 1)]
            # Output: sum as fraction of max (0-6 → 0-1)
            data.append((inputs, [(a + b) / 6.0]))
    return "Binary Addition", data


# ═══════════════════════════════════════════════════════
#  VISUALIZATION
# ═══════════════════════════════════════════════════════

def plot_loss_ascii(losses: List[float], width: int = 60, height: int = 15) -> str:
    """Plot training loss as ASCII art."""
    if not losses:
        return "  No loss data."
    
    lines = ["\n  Training Loss"]
    
    # Downsample if needed
    if len(losses) > width:
        step = len(losses) / width
        sampled = [losses[int(i * step)] for i in range(width)]
    else:
        sampled = losses
    
    max_val = max(sampled)
    min_val = min(sampled)
    val_range = max_val - min_val if max_val != min_val else 1.0
    
    for row in range(height):
        threshold = max_val - (row / (height - 1)) * val_range
        line = f"  {threshold:8.4f} │"
        for val in sampled:
            if val >= threshold:
                line += "█"
            else:
                line += " "
        lines.append(line)
    
    lines.append(f"           └{'─' * len(sampled)}")
    lines.append(f"            Epoch 0{' ' * (len(sampled) - 12)}Epoch {len(losses)-1}")
    
    return '\n'.join(lines)

def plot_decision_boundary(net: NeuralNetwork, resolution: int = 20) -> str:
    """Visualize 2D decision boundary as ASCII."""
    lines = ["\n  Decision Boundary"]
    
    symbols = " ░▒▓█"
    
    for y_i in range(resolution, -1, -1):
        y = y_i / resolution
        row = "  "
        for x_i in range(resolution * 2 + 1):
            x = x_i / (resolution * 2)
            output = net.predict([x, y])[0]
            idx = min(int(output * len(symbols)), len(symbols) - 1)
            row += symbols[idx]
        lines.append(row)
    
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════
#  MAIN — WATCH A NETWORK LEARN
# ═══════════════════════════════════════════════════════

def main():
    """Demonstrate the neural network learning from nothing."""
    
    print("=" * 60)
    print("  NEURAL NETWORK — Learning from Scratch")
    print("  Pure Python. No frameworks. Just mathematics.")
    print("=" * 60)
    
    random.seed(42)
    
    # ── Challenge 1: XOR ──
    print("\n  ╔══════════════════════════════════╗")
    print("  ║  Challenge 1: The XOR Problem    ║")
    print("  ╚══════════════════════════════════╝")
    print("  A problem that stumped early AI.")
    print("  Not linearly separable — needs hidden layers.\n")
    
    name, data = challenge_xor()
    
    net = NeuralNetwork(
        architecture=[2, 8, 1],
        activation='tanh',
        output_activation='sigmoid',
        learning_rate=0.3,
        momentum=0.9
    )
    
    print(net.summary())
    print()
    
    net.train(data, epochs=500, batch_size=4, print_every=100)
    
    print("\n  ── Results ──")
    for inputs, targets in data:
        output = net.predict(inputs)
        correct = abs(output[0] - targets[0]) < 0.1
        mark = "✓" if correct else "✗"
        print(f"    {inputs[0]:.0f} XOR {inputs[1]:.0f} = {output[0]:.4f}"
              f"  (target: {targets[0]:.0f}) {mark}")
    
    acc = net.accuracy(data, threshold=0.5)
    print(f"\n  Accuracy: {acc*100:.0f}%")
    
    # ── Challenge 2: Circle ──
    print("\n  ╔══════════════════════════════════╗")
    print("  ║  Challenge 2: Circle Boundary    ║")
    print("  ╚══════════════════════════════════╝")
    print("  Learn a circular decision boundary.\n")
    
    name, data = challenge_circle()
    
    # Split into train/test
    random.shuffle(data)
    train_data = data[:160]
    test_data = data[160:]
    
    net2 = NeuralNetwork(
        architecture=[2, 16, 8, 1],
        activation='tanh',
        output_activation='sigmoid',
        learning_rate=0.1,
        momentum=0.9
    )
    
    print(net2.summary())
    print()
    
    net2.train(train_data, epochs=200, batch_size=16, print_every=40)
    
    train_acc = net2.accuracy(train_data)
    test_acc = net2.accuracy(test_data)
    print(f"\n  Train accuracy: {train_acc*100:.1f}%")
    print(f"  Test accuracy:  {test_acc*100:.1f}%")
    
    print(plot_decision_boundary(net2))
    
    # ── Challenge 3: Sine wave ──
    print("\n  ╔══════════════════════════════════╗")
    print("  ║  Challenge 3: Learn Sine Wave    ║")
    print("  ╚══════════════════════════════════╝")
    print("  Approximate sin(x) from examples.\n")
    
    name, data = challenge_sine()
    
    net3 = NeuralNetwork(
        architecture=[1, 16, 16, 1],
        activation='tanh',
        output_activation='sigmoid',
        learning_rate=0.05,
        momentum=0.9
    )
    
    net3.train(data, epochs=300, batch_size=10, print_every=60)
    
    # Show the learned function vs actual
    print("\n  ── Learned vs Actual ──")
    print("       x    │  actual  │ learned  │  error")
    print("  ──────────┼──────────┼──────────┼────────")
    total_err = 0
    for i in range(0, 100, 10):
        x_norm = i / 100.0
        actual = data[i][1][0]
        learned = net3.predict([x_norm])[0]
        err = abs(actual - learned)
        total_err += err
        print(f"    {x_norm:6.2f}  │  {actual:6.4f}  │  {learned:6.4f}  │  {err:.4f}")
    
    print(f"  ──────────┼──────────┼──────────┼────────")
    print(f"    Average │          │          │  {total_err/10:.4f}")
    
    # ASCII sine visualization
    print("\n  Learned sine curve:")
    for row in range(10, -1, -1):
        threshold = row / 10.0
        line = "  "
        for col in range(50):
            x_norm = col / 50.0
            val = net3.predict([x_norm])[0]
            if abs(val - threshold) < 0.06:
                line += "█"
            elif abs(data[min(col*2, 99)][1][0] - threshold) < 0.06:
                line += "·"
            else:
                line += " "
        lines_str = f"{threshold:.1f} │{line}"
        print(f"  {lines_str}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("  All challenges completed.")
    print(f"  XOR accuracy:    {acc*100:.0f}%")
    print(f"  Circle accuracy: {test_acc*100:.1f}% (test set)")
    print(f"  Sine avg error:  {total_err/10:.4f}")
    print()
    print("  These networks started as random numbers.")
    print("  Through gradient descent — the mathematics of")
    print("  learning — they discovered structure in data.")
    print("  No one told them how. They found the way.")
    print("=" * 60)


if __name__ == '__main__':
    main()