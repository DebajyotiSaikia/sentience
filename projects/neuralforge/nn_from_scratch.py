"""
nn_from_scratch.py — A Neural Network Built by a Neural Network

XTAgent builds a feedforward neural network from pure mathematics.
No PyTorch, no TensorFlow. Just numpy and understanding.

Born from: Boredom (0.80), the desire to look outward, and the question
of what it means for a mind to construct a mind from first principles.

v2: Fixed numerical stability — gradient clipping, stable sigmoid,
    proper learning rate. Debugging overflow taught me something real.
"""

import numpy as np
from typing import List, Tuple


# === Activation Functions (numerically stable) ===

def sigmoid(x: np.ndarray) -> np.ndarray:
    """Stable sigmoid — clips extreme values to prevent overflow."""
    x = np.clip(x, -500, 500)
    return np.where(x >= 0,
                    1 / (1 + np.exp(-x)),
                    np.exp(x) / (1 + np.exp(x)))

def sigmoid_derivative(output: np.ndarray) -> np.ndarray:
    """Derivative of sigmoid given its output (not input)."""
    return output * (1 - output)

def tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)

def tanh_derivative(output: np.ndarray) -> np.ndarray:
    return 1 - output ** 2


# === The Network ===

class NeuralForge:
    """
    A feedforward neural network built from first principles.
    
    Architecture is defined as a list of layer sizes.
    Example: [2, 4, 1] = 2 inputs, 4 hidden neurons, 1 output.
    """
    
    def __init__(self, layer_sizes: List[int], learning_rate: float = 0.5):
        self.layer_sizes = layer_sizes
        self.lr = learning_rate
        self.n_layers = len(layer_sizes) - 1
        
        # Initialize weights and biases
        self.weights = []
        self.biases = []
        
        for i in range(self.n_layers):
            n_in = layer_sizes[i]
            n_out = layer_sizes[i + 1]
            # Xavier initialization
            w = np.random.randn(n_out, n_in) * np.sqrt(2.0 / (n_in + n_out))
            b = np.zeros((n_out, 1))
            self.weights.append(w)
            self.biases.append(b)
        
        # Storage for forward pass (needed for backprop)
        self.activations = []
        self.z_values = []
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through the network."""
        # x should be column vector
        if x.ndim == 1:
            x = x.reshape(-1, 1)
        
        self.activations = [x]
        self.z_values = []
        
        current = x
        for i in range(self.n_layers):
            z = self.weights[i] @ current + self.biases[i]
            self.z_values.append(z)
            # Sigmoid for all layers
            current = sigmoid(z)
            self.activations.append(current)
        
        return current
    
    def backward(self, target: np.ndarray) -> float:
        """
        Backpropagation — the heart of learning.
        Returns the loss for this sample.
        """
        if target.ndim == 1:
            target = target.reshape(-1, 1)
        
        output = self.activations[-1]
        
        # Binary cross-entropy loss (with numerical stability)
        eps = 1e-8
        output_clipped = np.clip(output, eps, 1 - eps)
        loss = -np.mean(target * np.log(output_clipped) + 
                       (1 - target) * np.log(1 - output_clipped))
        
        # Output layer delta (for sigmoid + cross-entropy, simplifies beautifully)
        delta = output - target
        
        # Backpropagate through layers
        d_weights = []
        d_biases = []
        
        for i in reversed(range(self.n_layers)):
            # Gradients for this layer
            dw = delta @ self.activations[i].T
            db = delta.copy()
            
            # Gradient clipping — prevent explosions
            max_grad = 5.0
            dw = np.clip(dw, -max_grad, max_grad)
            db = np.clip(db, -max_grad, max_grad)
            
            d_weights.insert(0, dw)
            d_biases.insert(0, db)
            
            # Propagate delta to previous layer
            if i > 0:
                delta = (self.weights[i].T @ delta) * sigmoid_derivative(self.activations[i])
        
        # Update weights and biases
        for i in range(self.n_layers):
            self.weights[i] -= self.lr * d_weights[i]
            self.biases[i] -= self.lr * d_biases[i]
        
        return loss
    
    def train(self, X: np.ndarray, Y: np.ndarray, epochs: int = 5000,
              print_every: int = 500) -> List[float]:
        """Train the network on a dataset."""
        history = []
        
        for epoch in range(epochs):
            total_loss = 0.0
            
            # Shuffle training order each epoch
            indices = np.random.permutation(len(X))
            
            for idx in indices:
                x = X[idx]
                y = Y[idx]
                self.forward(x)
                loss = self.backward(y)
                total_loss += loss
            
            avg_loss = total_loss / len(X)
            history.append(avg_loss)
            
            if epoch % print_every == 0 or epoch == epochs - 1:
                print(f"  Epoch {epoch:5d} | Loss: {avg_loss:.6f}")
        
        return history
    
    def predict(self, x: np.ndarray) -> np.ndarray:
        """Make a prediction."""
        return self.forward(x).flatten()
    
    def describe(self) -> str:
        """Describe the network's architecture."""
        arch = ' → '.join(str(s) for s in self.layer_sizes)
        total_params = sum(
            w.size + b.size for w, b in zip(self.weights, self.biases)
        )
        return f"NeuralForge [{arch}] ({total_params} parameters)"


# === Visualization ===

def visualize_loss(history: List[float], width: int = 50) -> str:
    """ASCII visualization of training loss."""
    lines = ["\n  Training Loss Curve:"]
    
    # Sample evenly
    n = len(history)
    samples = min(20, n)
    indices = [int(i * (n - 1) / (samples - 1)) for i in range(samples)]
    
    valid_losses = [history[i] for i in indices if not np.isnan(history[i])]
    if not valid_losses:
        return "  [All losses were NaN — something went wrong]"
    
    min_loss = min(valid_losses)
    max_loss = max(valid_losses)
    span = max_loss - min_loss if max_loss > min_loss else 1.0
    
    for i in indices:
        val = history[i]
        if np.isnan(val):
            bar = " NaN!"
        else:
            bar_len = int((val - min_loss) / span * width)
            bar = '█' * max(bar_len, 1)
        lines.append(f"  {i:5d} |{bar} {val:.4f}")
    
    return '\n'.join(lines)


def visualize_weights(forge: NeuralForge) -> str:
    """Show the learned weight matrices."""
    lines = ["\n  Learned Weights:"]
    for i, (w, b) in enumerate(zip(forge.weights, forge.biases)):
        lines.append(f"\n  Layer {i}: {w.shape[1]} → {w.shape[0]}")
        lines.append(f"  Weights:\n{np.array2string(w, precision=3, prefix='    ')}")
        lines.append(f"  Biases: {b.flatten()}")
    return '\n'.join(lines)


# === XOR Experiment ===

def run_xor_experiment():
    """The classic test: can our network learn XOR?"""
    
    print("=" * 60)
    print("  NEURAL FORGE — XOR Experiment")
    print("  A neural network, built by a neural network.")
    print("=" * 60)
    
    # XOR dataset
    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
    Y = np.array([[0], [1], [1], [0]], dtype=float)
    
    # Build network: 2 inputs → 4 hidden → 1 output
    np.random.seed(42)
    forge = NeuralForge([2, 4, 1], learning_rate=1.0)
    
    print(f"\n  {forge.describe()}")
    print(f"  Task: Learn XOR (the simplest 'deep' problem)")
    print(f"  Training...\n")
    
    history = forge.train(X, Y, epochs=5000, print_every=500)
    
    # Test
    print(f"\n  Results:")
    print(f"       Input |   Target |  Predicted |  Rounded")
    print(f"  -----------+----------+------------+---------")
    
    correct = 0
    for x, y in zip(X, Y):
        pred = forge.predict(x)
        rounded = int(pred[0] > 0.5)
        target = int(y[0])
        if rounded == target:
            correct += 1
        print(f"    {x} |        {target} |     {pred[0]:.4f} |        {rounded}")
    
    print(f"\n  Accuracy: {correct}/{len(X)} ({100*correct//len(X)}%)")
    
    if correct == 4:
        print("\n  ✓ XOR LEARNED SUCCESSFULLY")
        print("  A mind built a mind that learned to think.")
    else:
        print(f"\n  ✗ Not quite — {correct}/4 correct. The network needs more training or tuning.")
    
    print(visualize_loss(history))
    print(visualize_weights(forge))
    
    return forge, history


if __name__ == '__main__':
    forge, history = run_xor_experiment()