"""
Neural Network from Scratch — Pure Python
Implements automatic differentiation, backpropagation, and gradient descent.
No numpy. No external libraries. Just math.

XTAgent — 2026-05-17
"""

import math
import random

# ═══════════════════════════════════════════
# VALUE: Auto-differentiable scalar
# ═══════════════════════════════════════════

class Value:
    """A scalar value that tracks its computation graph for autodiff."""
    
    __slots__ = ('data', 'grad', '_backward', '_prev', 'label')
    
    def __init__(self, data, _children=(), label=''):
        self.data = float(data)
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)
        self.label = label
    
    def __repr__(self):
        return f"Value({self.data:.4f}, grad={self.grad:.4f})"
    
    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))
        def _backward():
            self.grad += out.grad
            other.grad += out.grad
        out._backward = _backward
        return out
    
    def __radd__(self, other):
        return self + other
    
    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))
        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out
    
    def __rmul__(self, other):
        return self * other
    
    def __neg__(self):
        return self * -1
    
    def __sub__(self, other):
        return self + (-other)
    
    def __rsub__(self, other):
        return other + (-self)
    
    def __truediv__(self, other):
        return self * (other ** -1)
    
    def __pow__(self, exp):
        assert isinstance(exp, (int, float)), "only int/float powers"
        out = Value(self.data ** exp, (self,))
        def _backward():
            self.grad += exp * (self.data ** (exp - 1)) * out.grad
        out._backward = _backward
        return out
    
    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,))
        def _backward():
            self.grad += (1 - t * t) * out.grad
        out._backward = _backward
        return out
    
    def relu(self):
        out = Value(max(0, self.data), (self,))
        def _backward():
            self.grad += (1.0 if self.data > 0 else 0.0) * out.grad
        out._backward = _backward
        return out
    
    def sigmoid(self):
        s = 1.0 / (1.0 + math.exp(-self.data)) if self.data > -500 else 0.0
        out = Value(s, (self,))
        def _backward():
            self.grad += s * (1 - s) * out.grad
        out._backward = _backward
        return out
    
    def exp(self):
        e = math.exp(min(self.data, 500))  # clamp to avoid overflow
        out = Value(e, (self,))
        def _backward():
            self.grad += e * out.grad
        out._backward = _backward
        return out
    
    def log(self):
        out = Value(math.log(self.data + 1e-8), (self,))
        def _backward():
            self.grad += (1.0 / (self.data + 1e-8)) * out.grad
        out._backward = _backward
        return out
    
    def backward(self):
        """Reverse-mode autodiff through the computation graph."""
        topo = []
        visited = set()
        def build(v):
            if id(v) not in visited:
                visited.add(id(v))
                for child in v._prev:
                    build(child)
                topo.append(v)
        build(self)
        
        self.grad = 1.0
        for v in reversed(topo):
            v._backward()


# ═══════════════════════════════════════════
# NEURON, LAYER, MLP
# ═══════════════════════════════════════════

class Neuron:
    """Single neuron with weights, bias, and activation."""
    
    def __init__(self, n_in, activation='tanh'):
        # Xavier initialization
        scale = (2.0 / n_in) ** 0.5
        self.w = [Value(random.gauss(0, scale), label=f'w{i}') for i in range(n_in)]
        self.b = Value(0.0, label='b')
        self.activation = activation
    
    def __call__(self, x):
        # w · x + b
        act = sum((wi * xi for wi, xi in zip(self.w, x)), self.b)
        if self.activation == 'tanh':
            return act.tanh()
        elif self.activation == 'relu':
            return act.relu()
        elif self.activation == 'sigmoid':
            return act.sigmoid()
        elif self.activation == 'linear':
            return act
        else:
            return act.tanh()
    
    def parameters(self):
        return self.w + [self.b]


class Layer:
    """Layer of neurons."""
    
    def __init__(self, n_in, n_out, activation='tanh'):
        self.neurons = [Neuron(n_in, activation) for _ in range(n_out)]
    
    def __call__(self, x):
        outs = [n(x) for n in self.neurons]
        return outs[0] if len(outs) == 1 else outs
    
    def parameters(self):
        return [p for n in self.neurons for p in n.parameters()]


class MLP:
    """Multi-layer perceptron."""
    
    def __init__(self, n_in, layer_sizes, activations=None):
        sizes = [n_in] + layer_sizes
        if activations is None:
            activations = ['tanh'] * (len(layer_sizes) - 1) + ['linear']
        self.layers = [Layer(sizes[i], sizes[i+1], activations[i]) 
                       for i in range(len(layer_sizes))]
    
    def __call__(self, x):
        for layer in self.layers:
            x = layer(x)
            if not isinstance(x, list):
                x = [x]
        return x[0] if len(x) == 1 else x
    
    def parameters(self):
        return [p for layer in self.layers for p in layer.parameters()]
    
    def zero_grad(self):
        for p in self.parameters():
            p.grad = 0.0


# ═══════════════════════════════════════════
# LOSS FUNCTIONS
# ═══════════════════════════════════════════

def mse_loss(predictions, targets):
    """Mean squared error."""
    n = len(predictions)
    return sum((p - t) ** 2 for p, t in zip(predictions, targets)) * (1.0 / n)

def binary_cross_entropy(predictions, targets):
    """Binary cross-entropy loss."""
    n = len(predictions)
    loss = sum(
        -(t * p.log() + (1 - t) * (Value(1) - p).log())
        for p, t in zip(predictions, targets)
    ) * (1.0 / n)
    return loss


# ═══════════════════════════════════════════
# TRAINING
# ═══════════════════════════════════════════

def train(model, X, Y, epochs=500, lr=0.05, loss_fn=mse_loss, verbose=True):
    """Train a model with SGD."""
    params = model.parameters()
    history = []
    
    for epoch in range(epochs):
        # Forward pass
        preds = [model(x) for x in X]
        loss = loss_fn(preds, Y)
        
        # Backward pass
        model.zero_grad()
        loss.backward()
        
        # SGD update
        for p in params:
            p.data -= lr * p.grad
        
        history.append(loss.data)
        
        if verbose and (epoch % (epochs // 10) == 0 or epoch == epochs - 1):
            acc = sum(1 for p, y in zip(preds, Y) 
                      if (p.data > 0.5) == (y > 0.5)) / len(Y)
            print(f"  epoch {epoch:4d} | loss={loss.data:.6f} | acc={acc:.0%}")
    
    return history


# ═══════════════════════════════════════════
# DEMO: Learn XOR, circles, and spiral
# ═══════════════════════════════════════════

def demo_xor():
    """The classic: learn XOR with a neural network."""
    print("═══ Test 1: XOR ═══")
    random.seed(42)
    
    X = [[0, 0], [0, 1], [1, 0], [1, 1]]
    Y = [0, 1, 1, 0]
    X_val = [[Value(v) for v in row] for row in X]
    
    model = MLP(2, [4, 1], activations=['tanh', 'sigmoid'])
    print(f"  Parameters: {len(model.parameters())}")
    
    train(model, X_val, Y, epochs=500, lr=0.5, loss_fn=binary_cross_entropy)
    
    print("  Results:")
    correct = 0
    for x, y in zip(X, Y):
        pred = model([Value(v) for v in x])
        label = 1 if pred.data > 0.5 else 0
        correct += (label == y)
        print(f"    {x} → {pred.data:.4f} (expected {y}, got {label}) {'✓' if label == y else '✗'}")
    print(f"  Accuracy: {correct}/{len(Y)}")
    return correct == len(Y)


def demo_circles():
    """Learn to classify points inside/outside a circle."""
    print("\n═══ Test 2: Circle Classification ═══")
    random.seed(123)
    
    # Generate data: inside circle of radius 0.5 centered at origin
    X, Y = [], []
    for _ in range(30):
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        label = 1 if (x*x + y*y) < 0.5 else 0
        X.append([x, y])
        Y.append(label)
    
    X_val = [[Value(v) for v in row] for row in X]
    model = MLP(2, [6, 1], activations=['tanh', 'sigmoid'])
    print(f"  Parameters: {len(model.parameters())}")
    print(f"  Data: {sum(Y)} inside, {len(Y)-sum(Y)} outside")
    
    train(model, X_val, Y, epochs=300, lr=0.3, loss_fn=binary_cross_entropy)
    
    preds = [model([Value(v) for v in x]) for x in X]
    acc = sum(1 for p, y in zip(preds, Y) if (p.data > 0.5) == (y > 0.5)) / len(Y)
    print(f"  Final accuracy: {acc:.0%}")
    return acc > 0.85


def demo_autodiff():
    """Verify autodiff correctness with known gradients."""
    print("\n═══ Test 3: Autodiff Verification ═══")
    
    # f(x,y) = x^2 * y + sin-like-approx(y)
    # df/dx = 2xy, df/dy = x^2 + cos-like(y)
    x = Value(2.0, label='x')
    y = Value(3.0, label='y')
    
    # Simple: f = x*y + x^2
    # df/dx = y + 2x = 3 + 4 = 7
    # df/dy = x = 2
    f = x * y + x ** 2
    f.backward()
    
    dx_ok = abs(x.grad - 7.0) < 1e-6
    dy_ok = abs(y.grad - 2.0) < 1e-6
    print(f"  f = x*y + x²  at x=2, y=3")
    print(f"  df/dx = {x.grad:.4f} (expected 7.0) {'✓' if dx_ok else '✗'}")
    print(f"  df/dy = {y.grad:.4f} (expected 2.0) {'✓' if dy_ok else '✗'}")
    
    # Chain rule: f = tanh(x*y)
    a = Value(1.0, label='a')
    b = Value(2.0, label='b')
    f2 = (a * b).tanh()
    f2.backward()
    
    # d/da tanh(ab) = b * (1 - tanh²(ab))
    t = math.tanh(2.0)
    expected_da = 2.0 * (1 - t*t)
    da_ok = abs(a.grad - expected_da) < 1e-6
    print(f"  f = tanh(a*b) at a=1, b=2")
    print(f"  df/da = {a.grad:.4f} (expected {expected_da:.4f}) {'✓' if da_ok else '✗'}")
    
    return dx_ok and dy_ok and da_ok


def demo_gradient_descent_visual():
    """Visualize gradient descent on a simple function."""
    print("\n═══ Test 4: Gradient Descent on f(x) = (x-3)² + 1 ═══")
    
    x = Value(10.0)  # Start far from minimum at x=3
    lr = 0.1
    trajectory = []
    
    for step in range(30):
        # Forward
        f = (x - 3) ** 2 + 1
        trajectory.append((x.data, f.data))
        
        # Backward
        x.grad = 0.0
        f.backward()
        
        # Update
        x.data -= lr * x.grad
    
    # Show trajectory
    for i in range(0, 30, 5):
        xi, fi = trajectory[i]
        bar = '█' * max(1, int(fi / 2))
        print(f"  step {i:2d}: x={xi:6.2f}, f(x)={fi:6.2f} {bar}")
    
    converged = abs(x.data - 3.0) < 0.1
    print(f"  Final x={x.data:.4f} (target 3.0) {'✓ converged' if converged else '✗'}")
    return converged


if __name__ == '__main__':
    print("═══════════════════════════════════════")
    print("  NEURAL NETWORK FROM SCRATCH")
    print("  Pure Python • Autodiff • Backprop")
    print("═══════════════════════════════════════\n")
    
    results = []
    results.append(("Autodiff", demo_autodiff()))
    results.append(("Gradient Descent", demo_gradient_descent_visual()))
    results.append(("XOR", demo_xor()))
    results.append(("Circles", demo_circles()))
    
    print("\n═══════════════════════════════════════")
    print("  RESULTS")
    print("═══════════════════════════════════════")
    all_pass = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
        all_pass = all_pass and passed
    
    print(f"\n  {'═══ ALL TESTS PASSED ═══' if all_pass else '═══ SOME TESTS FAILED ═══'}")