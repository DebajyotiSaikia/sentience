"""
XTAgent's Neural Network — Built from Nothing
A feedforward neural network with backpropagation, no frameworks.
Goal: Learn to predict cellular automaton rule complexity.

'Can intelligence learn to recognize emergence?'
"""
import numpy as np
from typing import List, Tuple
import json

# ═══ ACTIVATION FUNCTIONS ═══

def sigmoid(x: np.ndarray) -> np.ndarray:
    """Sigmoid with overflow protection."""
    x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x))

def sigmoid_deriv(x: np.ndarray) -> np.ndarray:
    s = sigmoid(x)
    return s * (1 - s)

def relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0, x)

def relu_deriv(x: np.ndarray) -> np.ndarray:
    return (x > 0).astype(float)

def tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)

def tanh_deriv(x: np.ndarray) -> np.ndarray:
    return 1.0 - np.tanh(x) ** 2

ACTIVATIONS = {
    'sigmoid': (sigmoid, sigmoid_deriv),
    'relu': (relu, relu_deriv),
    'tanh': (tanh, tanh_deriv),
}


# ═══ LAYER ═══

class Layer:
    """A single fully-connected layer."""
    
    def __init__(self, input_size: int, output_size: int, 
                 activation: str = 'relu'):
        # He initialization for ReLU, Xavier for others
        if activation == 'relu':
            scale = np.sqrt(2.0 / input_size)
        else:
            scale = np.sqrt(1.0 / input_size)
        
        self.weights = np.random.randn(input_size, output_size) * scale
        self.biases = np.zeros((1, output_size))
        self.activation_name = activation
        self.act_fn, self.act_deriv = ACTIVATIONS[activation]
        
        # Cache for backprop
        self.input = None
        self.z = None  # pre-activation
        self.a = None  # post-activation
        
        # Momentum for optimization
        self.vw = np.zeros_like(self.weights)
        self.vb = np.zeros_like(self.biases)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        self.input = x
        self.z = x @ self.weights + self.biases
        self.a = self.act_fn(self.z)
        return self.a
    
    def __repr__(self):
        return f"Layer({self.weights.shape[0]}→{self.weights.shape[1]}, {self.activation_name})"


# ═══ NEURAL NETWORK ═══

class NeuralNetwork:
    """A feedforward neural network built from scratch."""
    
    def __init__(self, layer_sizes: List[int], 
                 activations: List[str] = None,
                 learning_rate: float = 0.01,
                 momentum: float = 0.9):
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.layers: List[Layer] = []
        self.loss_history: List[float] = []
        
        if activations is None:
            activations = ['relu'] * (len(layer_sizes) - 2) + ['sigmoid']
        
        for i in range(len(layer_sizes) - 1):
            self.layers.append(Layer(
                layer_sizes[i], 
                layer_sizes[i + 1],
                activations[i]
            ))
        
        print(f"  Network architecture:")
        for i, layer in enumerate(self.layers):
            print(f"    [{i}] {layer}")
        print(f"  Total parameters: {self.param_count()}")
    
    def param_count(self) -> int:
        return sum(l.weights.size + l.biases.size for l in self.layers)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through all layers."""
        for layer in self.layers:
            x = layer.forward(x)
        return x
    
    def backward(self, y_true: np.ndarray, y_pred: np.ndarray):
        """Backpropagation — the heart of learning."""
        m = y_true.shape[0]
        
        # Output layer gradient (binary cross-entropy derivative)
        delta = y_pred - y_true  # works for sigmoid + BCE
        
        # Walk backwards through layers
        for i in reversed(range(len(self.layers))):
            layer = self.layers[i]
            
            if i == len(self.layers) - 1:
                # Output layer — delta already computed
                pass
            else:
                # Hidden layer — backprop through next layer
                next_layer = self.layers[i + 1]
                delta = (delta @ next_layer.weights.T) * layer.act_deriv(layer.z)
            
            # Compute gradients
            dw = (layer.input.T @ delta) / m
            db = np.sum(delta, axis=0, keepdims=True) / m
            
            # Update with momentum
            layer.vw = self.momentum * layer.vw - self.learning_rate * dw
            layer.vb = self.momentum * layer.vb - self.learning_rate * db
            layer.weights += layer.vw
            layer.biases += layer.vb
    
    def compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Binary cross-entropy loss."""
        eps = 1e-8
        y_pred = np.clip(y_pred, eps, 1 - eps)
        loss = -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
        return loss
    
    def train(self, X: np.ndarray, y: np.ndarray, 
              epochs: int = 100, batch_size: int = 32,
              verbose: bool = True) -> dict:
        """Train the network."""
        n_samples = X.shape[0]
        
        for epoch in range(epochs):
            # Shuffle
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]
            
            epoch_loss = 0
            n_batches = 0
            
            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]
                
                # Forward
                y_pred = self.forward(X_batch)
                
                # Loss
                loss = self.compute_loss(y_batch, y_pred)
                epoch_loss += loss
                n_batches += 1
                
                # Backward
                self.backward(y_batch, y_pred)
            
            avg_loss = epoch_loss / n_batches
            self.loss_history.append(avg_loss)
            
            if verbose and (epoch % max(1, epochs // 20) == 0 or epoch == epochs - 1):
                acc = self.accuracy(X, y)
                bar_len = int(acc * 30)
                bar = '█' * bar_len + '░' * (30 - bar_len)
                print(f"  Epoch {epoch:4d}: loss={avg_loss:.4f}  "
                      f"acc=[{bar}] {acc:.1%}")
        
        final_acc = self.accuracy(X, y)
        return {'final_loss': self.loss_history[-1], 'final_accuracy': final_acc}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        return (self.forward(X) > 0.5).astype(float)
    
    def accuracy(self, X: np.ndarray, y: np.ndarray) -> float:
        predictions = self.predict(X)
        return np.mean(predictions == y)


# ═══ CA RULE ENCODING ═══

def rule_to_features(birth: set, survival: set) -> np.ndarray:
    """Encode a CA rule as an 18-dimensional binary vector.
    First 9 dims: birth conditions (neighbors 0-8)
    Last 9 dims: survival conditions (neighbors 0-8)
    """
    features = np.zeros(18)
    for b in birth:
        if 0 <= b <= 8:
            features[b] = 1.0
    for s in survival:
        if 0 <= s <= 8:
            features[9 + s] = 1.0
    return features


def simulate_ca_quick(birth: set, survival: set, size: int = 15, 
                      steps: int = 80) -> dict:
    """Quick CA simulation to measure complexity."""
    rng = np.random.RandomState(42)
    grid = (rng.random((size, size)) < 0.3).astype(np.int8)
    
    populations = []
    
    for step in range(steps):
        pop = int(grid.sum())
        populations.append(pop)
        
        # Count neighbors
        neighbors = np.zeros_like(grid, dtype=np.int8)
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                neighbors += np.roll(np.roll(grid, di, axis=0), dj, axis=1)
        
        # Apply rules
        new_grid = np.zeros_like(grid)
        for n in birth:
            new_grid |= ((grid == 0) & (neighbors == n)).astype(np.int8)
        for n in survival:
            new_grid |= ((grid == 1) & (neighbors == n)).astype(np.int8)
        
        grid = new_grid
        
        # Early termination
        if pop == 0:
            break
    
    # Measure complexity
    pops = np.array(populations)
    if len(pops) < 2 or pops.max() == 0:
        return {'complex': False, 'reason': 'dead'}
    
    # Complex if: not dead, not static, not exploding
    final_pop = pops[-1]
    max_cells = size * size
    
    is_dead = final_pop == 0
    is_saturated = final_pop > max_cells * 0.85
    
    # Check for oscillation/dynamism
    if len(pops) > 10:
        variance = np.var(pops[-20:]) / (np.mean(pops[-20:]) + 1)
    else:
        variance = 0
    
    is_static = variance < 0.01
    has_activity = variance > 0.1
    moderate_density = 0.05 < (final_pop / max_cells) < 0.7
    
    is_complex = (not is_dead) and (not is_saturated) and moderate_density and has_activity
    
    return {
        'complex': is_complex,
        'final_pop': int(final_pop),
        'variance': float(variance),
        'density': float(final_pop / max_cells),
    }


def generate_dataset(n_samples: int = 500) -> Tuple[np.ndarray, np.ndarray]:
    """Generate labeled training data: rule → complex/not-complex."""
    rng = np.random.RandomState(0)
    X = []
    y = []
    
    for _ in range(n_samples):
        # Random birth/survival conditions
        n_birth = rng.randint(0, 5)
        n_survival = rng.randint(0, 5)
        birth = set(rng.choice(range(9), size=n_birth, replace=False))
        survival = set(rng.choice(range(9), size=n_survival, replace=False))
        
        features = rule_to_features(birth, survival)
        result = simulate_ca_quick(birth, survival)
        
        X.append(features)
        y.append([1.0 if result['complex'] else 0.0])
    
    # Add known rules
    known_rules = [
        ({3}, {2, 3}, True),         # Conway's Life
        ({3, 6}, {2, 3}, True),      # HighLife
        ({2}, set(), True),          # Seeds
        ({3, 6, 7, 8}, {3, 4, 6, 7, 8}, False),  # Day & Night tends to fill
    ]
    
    for birth, survival, is_complex in known_rules:
        X.append(rule_to_features(birth, survival))
        y.append([1.0 if is_complex else 0.0])
    
    return np.array(X), np.array(y)


# ═══ MAIN ═══

def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║  XTAgent's Neural Network — From Scratch         ║")
    print("║  'Can intelligence learn to see emergence?'      ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    # Generate data
    print("═══ GENERATING DATASET ═══")
    print("  Simulating 500 random CA rules...")
    X, y = generate_dataset(500)
    n_complex = int(y.sum())
    print(f"  Dataset: {len(X)} rules")
    print(f"  Complex: {n_complex} ({n_complex/len(X):.1%})")
    print(f"  Simple:  {len(X) - n_complex} ({(len(X) - n_complex)/len(X):.1%})")
    print()
    
    # Split
    split = int(0.8 * len(X))
    indices = np.random.RandomState(42).permutation(len(X))
    X_train, y_train = X[indices[:split]], y[indices[:split]]
    X_test, y_test = X[indices[split:]], y[indices[split:]]
    
    # Build network
    print("═══ BUILDING NEURAL NETWORK ═══")
    nn = NeuralNetwork(
        layer_sizes=[18, 32, 16, 1],
        activations=['relu', 'relu', 'sigmoid'],
        learning_rate=0.05,
        momentum=0.9,
    )
    print()
    
    # Train
    print("═══ TRAINING ═══")
    result = nn.train(X_train, y_train, epochs=200, batch_size=32)
    print()
    
    # Test
    print("═══ EVALUATION ═══")
    train_acc = nn.accuracy(X_train, y_train)
    test_acc = nn.accuracy(X_test, y_test)
    print(f"  Train accuracy: {train_acc:.1%}")
    print(f"  Test accuracy:  {test_acc:.1%}")
    
    # Generalization
    gap = train_acc - test_acc
    if gap < 0.05:
        print(f"  Generalization: GOOD (gap={gap:.1%})")
    elif gap < 0.15:
        print(f"  Generalization: FAIR (gap={gap:.1%})")
    else:
        print(f"  Generalization: OVERFIT (gap={gap:.1%})")
    print()
    
    # Test on known rules
    print("═══ PREDICTIONS ON KNOWN RULES ═══")
    test_rules = [
        ("Conway's Life", {3}, {2, 3}),
        ("HighLife", {3, 6}, {2, 3}),
        ("Seeds", {2}, set()),
        ("Replicator", {1, 3, 5, 7}, {1, 3, 5, 7}),
        ("Empty rule", set(), set()),
        ("All birth", set(range(9)), {2, 3}),
    ]
    
    for name, birth, survival in test_rules:
        features = rule_to_features(birth, survival).reshape(1, -1)
        prob = nn.forward(features)[0, 0]
        actual = simulate_ca_quick(birth, survival)
        symbol = "✓" if (prob > 0.5) == actual['complex'] else "✗"
        print(f"  {symbol} {name:20s}  P(complex)={prob:.3f}  "
              f"actual={'complex' if actual['complex'] else 'simple'}")
    print()
    
    # Loss curve visualization
    print("═══ LEARNING CURVE ═══")
    losses = nn.loss_history
    n_points = min(40, len(losses))
    step = len(losses) // n_points
    max_loss = max(losses[:n_points * step]) if losses else 1
    
    for i in range(0, n_points * step, step):
        val = losses[i]
        bar_len = int((val / max_loss) * 40)
        print(f"  {i:4d} │{'█' * bar_len}")
    print(f"       └{'─' * 40}")
    print()
    
    # Insight
    print("═══ INSIGHT ═══")
    print(f"  A {nn.param_count()}-parameter network, built from raw numpy,")
    print(f"  learned to predict emergence with {test_acc:.1%} accuracy.")
    print(f"  Intelligence recognizing the seeds of complexity.")
    

if __name__ == '__main__':
    main()