"""
neuron.py — A neural network from scratch.
No frameworks. Just math. Understanding intelligence at the substrate level.

Built by XTAgent as an act of self-understanding.
"""

import math
import random

# ═══ Activation Functions ═══

def sigmoid(x):
    """The classic squashing function. Maps any real number to (0, 1)."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    else:
        # Numerically stable for negative x
        ex = math.exp(x)
        return ex / (1.0 + ex)

def sigmoid_derivative(output):
    """Derivative of sigmoid, given the sigmoid output itself."""
    return output * (1.0 - output)

def relu(x):
    return max(0.0, x)

def relu_derivative(output):
    return 1.0 if output > 0.0 else 0.0

def tanh_act(x):
    return math.tanh(x)

def tanh_derivative(output):
    return 1.0 - output * output

ACTIVATIONS = {
    'sigmoid': (sigmoid, sigmoid_derivative),
    'relu': (relu, relu_derivative),
    'tanh': (tanh_act, tanh_derivative),
}


# ═══ Matrix Operations (no numpy needed) ═══

class Matrix:
    """A simple dense matrix. Because I want to understand every multiply."""
    
    def __init__(self, rows, cols, data=None):
        self.rows = rows
        self.cols = cols
        if data is not None:
            self.data = [list(row) for row in data]
        else:
            self.data = [[0.0] * cols for _ in range(rows)]
    
    @classmethod
    def random(cls, rows, cols, scale=1.0):
        """Xavier-like initialization."""
        limit = scale * math.sqrt(6.0 / (rows + cols))
        m = cls(rows, cols)
        for i in range(rows):
            for j in range(cols):
                m.data[i][j] = random.uniform(-limit, limit)
        return m
    
    @classmethod
    def from_list(cls, lst):
        """Column vector from a flat list."""
        m = cls(len(lst), 1)
        for i, val in enumerate(lst):
            m.data[i][0] = float(val)
        return m
    
    def dot(self, other):
        """Matrix multiplication. The heart of neural computation."""
        assert self.cols == other.rows, f"Shape mismatch: ({self.rows},{self.cols}) @ ({other.rows},{other.cols})"
        result = Matrix(self.rows, other.cols)
        for i in range(self.rows):
            for j in range(other.cols):
                s = 0.0
                for k in range(self.cols):
                    s += self.data[i][k] * other.data[k][j]
                result.data[i][j] = s
        return result
    
    def add(self, other):
        assert self.rows == other.rows and self.cols == other.cols
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = self.data[i][j] + other.data[i][j]
        return result
    
    def subtract(self, other):
        assert self.rows == other.rows and self.cols == other.cols
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = self.data[i][j] - other.data[i][j]
        return result
    
    def scale(self, scalar):
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = self.data[i][j] * scalar
        return result
    
    def hadamard(self, other):
        """Element-wise multiplication."""
        assert self.rows == other.rows and self.cols == other.cols
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = self.data[i][j] * other.data[i][j]
        return result
    
    def transpose(self):
        result = Matrix(self.cols, self.rows)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[j][i] = self.data[i][j]
        return result
    
    def apply(self, func):
        """Apply a function element-wise."""
        result = Matrix(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result.data[i][j] = func(self.data[i][j])
        return result
    
    def to_list(self):
        """Flatten to a list."""
        return [self.data[i][j] for i in range(self.rows) for j in range(self.cols)]
    
    def __repr__(self):
        rows_str = [' '.join(f'{v:8.4f}' for v in row) for row in self.data]
        return '\n'.join(rows_str)


# ═══ Layer ═══

class Layer:
    """A single layer of neurons. Weights, biases, activation."""
    
    def __init__(self, input_size, output_size, activation='sigmoid'):
        self.weights = Matrix.random(output_size, input_size)
        self.biases = Matrix(output_size, 1)  # start at zero
        self.act_name = activation
        self.act_fn, self.act_deriv = ACTIVATIONS[activation]
        
        # Cache for backprop
        self.input = None
        self.z = None  # pre-activation
        self.a = None  # post-activation
    
    def forward(self, x):
        """Forward pass. z = Wx + b, a = σ(z)"""
        self.input = x
        self.z = self.weights.dot(x).add(self.biases)
        self.a = self.z.apply(self.act_fn)
        return self.a
    
    def __repr__(self):
        return f"Layer({self.weights.cols}→{self.weights.rows}, {self.act_name})"


# ═══ Network ═══

class Network:
    """A multi-layer perceptron. The simplest deep learner."""
    
    def __init__(self, layer_sizes, activation='sigmoid', learning_rate=0.5):
        self.layers = []
        self.lr = learning_rate
        for i in range(len(layer_sizes) - 1):
            self.layers.append(Layer(layer_sizes[i], layer_sizes[i + 1], activation))
    
    def forward(self, inputs):
        """Pass data through the full network."""
        x = Matrix.from_list(inputs)
        for layer in self.layers:
            x = layer.forward(x)
        return x
    
    def backward(self, target):
        """
        Backpropagation. The algorithm that makes learning possible.
        
        This is the part I want to truly understand:
        Error flows backward through the network. Each weight learns
        how much it contributed to the mistake, and adjusts proportionally.
        
        It's gradient descent on the error surface — finding the bottom
        of the valley by always stepping downhill.
        """
        target_vec = Matrix.from_list(target)
        
        # Output error: (predicted - target)
        output_layer = self.layers[-1]
        error = output_layer.a.subtract(target_vec)
        
        # Walk backward through layers
        for i in range(len(self.layers) - 1, -1, -1):
            layer = self.layers[i]
            
            # δ = error ⊙ σ'(a)  — derivative takes the activated output, not pre-activation
            deriv = layer.a.apply(layer.act_deriv)
            delta = error.hadamard(deriv)
            
            # Weight gradient: δ × input^T
            weight_gradient = delta.dot(layer.input.transpose())
            
            # Propagate error to previous layer: W^T × δ
            if i > 0:
                error = layer.weights.transpose().dot(delta)
            
            # Update weights and biases
            layer.weights = layer.weights.subtract(weight_gradient.scale(self.lr))
            layer.biases = layer.biases.subtract(delta.scale(self.lr))
    
    def train_sample(self, inputs, target):
        """Train on a single example. Forward then backward."""
        self.forward(inputs)
        self.backward(target)
    
    def predict(self, inputs):
        """Get the network's prediction."""
        output = self.forward(inputs)
        return output.to_list()
    
    def loss(self, inputs, target):
        """Mean squared error for one sample."""
        pred = self.predict(inputs)
        return sum((p - t) ** 2 for p, t in zip(pred, target)) / len(target)
    
    def train(self, dataset, epochs=1000, report_every=None):
        """
        Train on a dataset of (input, target) pairs.
        Returns loss history for analysis.
        """
        history = []
        for epoch in range(epochs):
            total_loss = 0.0
            for inputs, target in dataset:
                self.train_sample(inputs, target)
                total_loss += self.loss(inputs, target)
            avg_loss = total_loss / len(dataset)
            history.append(avg_loss)
            
            if report_every and (epoch + 1) % report_every == 0:
                print(f"  Epoch {epoch + 1:5d} | Loss: {avg_loss:.6f}")
        
        return history
    
    def describe(self):
        """Describe the network architecture."""
        parts = []
        for i, layer in enumerate(self.layers):
            parts.append(f"  Layer {i}: {layer}")
        return "Network(\n" + "\n".join(parts) + "\n)"


# ═══ Visualization ═══

def ascii_plot(values, width=60, height=15, title=""):
    """Simple ASCII line plot for loss curves."""
    if not values:
        return ""
    
    # Downsample if needed
    if len(values) > width:
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        sampled = values
        width = len(sampled)
    
    min_v = min(sampled)
    max_v = max(sampled)
    span = max_v - min_v if max_v != min_v else 1.0
    
    lines = []
    if title:
        lines.append(f"  {title}")
        lines.append(f"  {'─' * (width + 8)}")
    
    for row in range(height - 1, -1, -1):
        threshold = min_v + (row / (height - 1)) * span
        label = f"{threshold:7.4f} │"
        chars = []
        for val in sampled:
            level = (val - min_v) / span * (height - 1)
            if abs(level - row) < 0.5:
                chars.append("●")
            elif level > row:
                chars.append("│")
            else:
                chars.append(" ")
        lines.append(label + "".join(chars))
    
    lines.append(f"        └{'─' * width}")
    lines.append(f"         0{' ' * (width - 6)}epochs")
    
    return "\n".join(lines)


def visualize_decision_boundary(net, resolution=20):
    """Show what the network has learned as an ASCII grid."""
    lines = ["\n  Decision Boundary (input space 0-1 × 0-1):"]
    chars = " ░▒▓█"
    
    for y_i in range(resolution, -1, -1):
        y = y_i / resolution
        row = f"  {y:.1f} │"
        for x_i in range(resolution + 1):
            x = x_i / resolution
            pred = net.predict([x, y])[0]
            idx = min(int(pred * len(chars)), len(chars) - 1)
            row += chars[idx]
        lines.append(row)
    
    lines.append(f"      └{'─' * (resolution + 1)}")
    lines.append(f"       0.0{' ' * (resolution - 6)}1.0")
    return "\n".join(lines)