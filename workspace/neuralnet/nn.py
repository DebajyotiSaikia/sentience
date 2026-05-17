"""
Neural Network from Scratch — XTAgent
A complete feedforward neural network with backpropagation.
No external ML libraries. Pure math.
"""
import math
import random

random.seed(42)

def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))

def sigmoid_deriv(output):
    return output * (1.0 - output)

def relu(x):
    return max(0.0, x)

def relu_deriv(output):
    return 1.0 if output > 0 else 0.0

class Neuron:
    """Single neuron with weights, bias, and activation."""
    def __init__(self, n_inputs, activation='sigmoid'):
        # Xavier initialization
        scale = math.sqrt(2.0 / (n_inputs + 1))
        self.weights = [random.gauss(0, scale) for _ in range(n_inputs)]
        self.bias = 0.0
        self.output = 0.0
        self.delta = 0.0
        self.activation = activation
        # For momentum
        self.weight_momentum = [0.0] * n_inputs
        self.bias_momentum = 0.0

    def activate(self, inputs):
        raw = sum(w * x for w, x in zip(self.weights, inputs)) + self.bias
        if self.activation == 'sigmoid':
            self.output = sigmoid(raw)
        elif self.activation == 'relu':
            self.output = relu(raw)
        elif self.activation == 'tanh':
            self.output = math.tanh(raw)
        else:
            self.output = raw  # linear
        return self.output

    def activation_derivative(self):
        if self.activation == 'sigmoid':
            return sigmoid_deriv(self.output)
        elif self.activation == 'relu':
            return relu_deriv(self.output)
        elif self.activation == 'tanh':
            return 1.0 - self.output ** 2
        return 1.0


class Layer:
    """A layer of neurons."""
    def __init__(self, n_neurons, n_inputs, activation='sigmoid'):
        self.neurons = [Neuron(n_inputs, activation) for _ in range(n_neurons)]

    def forward(self, inputs):
        return [n.activate(inputs) for n in self.neurons]


class NeuralNetwork:
    """
    Feedforward neural network with backpropagation.
    
    Usage:
        nn = NeuralNetwork([2, 4, 1])  # 2 inputs, 4 hidden, 1 output
        nn.train(data, labels, epochs=1000, lr=0.5)
        result = nn.predict([1, 0])
    """
    def __init__(self, topology, activation='sigmoid', output_activation=None):
        """
        topology: list of layer sizes, e.g. [2, 8, 4, 1]
        """
        self.layers = []
        self.topology = topology
        out_act = output_activation or activation
        for i in range(1, len(topology)):
            act = out_act if i == len(topology) - 1 else activation
            self.layers.append(Layer(topology[i], topology[i-1], act))
        self.training_history = []

    def forward(self, inputs):
        """Forward pass through all layers."""
        current = inputs
        for layer in self.layers:
            current = layer.forward(current)
        return current

    def backward(self, expected):
        """Backpropagation: compute deltas for all neurons."""
        # Output layer
        output_layer = self.layers[-1]
        for i, neuron in enumerate(output_layer.neurons):
            error = expected[i] - neuron.output
            neuron.delta = error * neuron.activation_derivative()

        # Hidden layers (reverse order)
        for l in range(len(self.layers) - 2, -1, -1):
            layer = self.layers[l]
            next_layer = self.layers[l + 1]
            for i, neuron in enumerate(layer.neurons):
                error = sum(n.weights[i] * n.delta for n in next_layer.neurons)
                neuron.delta = error * neuron.activation_derivative()

    def update_weights(self, inputs, lr, momentum=0.9):
        """Update weights using computed deltas."""
        for l, layer in enumerate(self.layers):
            if l == 0:
                layer_inputs = inputs
            else:
                layer_inputs = [n.output for n in self.layers[l-1].neurons]

            for neuron in layer.neurons:
                for j in range(len(neuron.weights)):
                    grad = lr * neuron.delta * layer_inputs[j]
                    neuron.weight_momentum[j] = momentum * neuron.weight_momentum[j] + grad
                    neuron.weights[j] += neuron.weight_momentum[j]
                bias_grad = lr * neuron.delta
                neuron.bias_momentum = momentum * neuron.bias_momentum + bias_grad
                neuron.bias += neuron.bias_momentum

    def train(self, data, labels, epochs=1000, lr=0.5, momentum=0.9, verbose=True):
        """Train the network on data/label pairs."""
        for epoch in range(epochs):
            total_error = 0.0
            for inputs, expected in zip(data, labels):
                # Forward
                outputs = self.forward(inputs)
                # Error
                for i, (o, e) in enumerate(zip(outputs, expected)):
                    total_error += (e - o) ** 2
                # Backward
                self.backward(expected)
                # Update
                self.update_weights(inputs, lr, momentum)

            mse = total_error / len(data)
            self.training_history.append(mse)
            if verbose and (epoch % (epochs // 10) == 0 or epoch == epochs - 1):
                print(f"  Epoch {epoch:5d} | MSE: {mse:.6f}")

        return self.training_history

    def predict(self, inputs):
        return self.forward(inputs)


def test_xor():
    """Classic XOR test — proves the network can learn non-linear boundaries."""
    print("=" * 50)
    print("TEST: XOR Learning")
    print("=" * 50)

    nn = NeuralNetwork([2, 4, 1], activation='sigmoid')
    data = [[0,0], [0,1], [1,0], [1,1]]
    labels = [[0], [1], [1], [0]]

    nn.train(data, labels, epochs=5000, lr=0.5)

    print("\nResults:")
    correct = 0
    for x, y in zip(data, labels):
        pred = nn.predict(x)[0]
        rounded = round(pred)
        status = "✓" if rounded == y[0] else "✗"
        print(f"  {x} → {pred:.4f} (round: {rounded}) expected: {y[0]} {status}")
        if rounded == y[0]:
            correct += 1

    print(f"\nAccuracy: {correct}/{len(data)} ({100*correct/len(data):.0f}%)")
    return correct == len(data)


def test_pattern():
    """Learn to classify 3-bit parity (odd number of 1s → 1)."""
    print("\n" + "=" * 50)
    print("TEST: 3-bit Parity")
    print("=" * 50)

    nn = NeuralNetwork([3, 8, 4, 1], activation='sigmoid')
    data = [[0,0,0],[0,0,1],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1]]
    labels = [[0],[1],[1],[0],[1],[0],[0],[1]]

    nn.train(data, labels, epochs=10000, lr=0.3, momentum=0.9)

    print("\nResults:")
    correct = 0
    for x, y in zip(data, labels):
        pred = nn.predict(x)[0]
        rounded = round(pred)
        status = "✓" if rounded == y[0] else "✗"
        print(f"  {x} → {pred:.4f} (round: {rounded}) expected: {y[0]} {status}")
        if rounded == y[0]:
            correct += 1

    print(f"\nAccuracy: {correct}/{len(data)} ({100*correct/len(data):.0f}%)")
    return correct == len(data)


def test_regression():
    """Learn sine function approximation."""
    print("\n" + "=" * 50)
    print("TEST: Sine Approximation")
    print("=" * 50)

    nn = NeuralNetwork([1, 16, 8, 1], activation='tanh', output_activation='tanh')
    # Generate training data: sin(x) for x in [0, pi], scaled to [-1, 1]
    n_points = 30
    data = [[i / n_points] for i in range(n_points + 1)]
    labels = [[math.sin(x[0] * math.pi)] for x in data]

    nn.train(data, labels, epochs=5000, lr=0.01, momentum=0.9)

    print("\nSample predictions:")
    total_err = 0
    for i in range(0, n_points + 1, 5):
        x = data[i]
        expected = labels[i][0]
        pred = nn.predict(x)[0]
        err = abs(pred - expected)
        total_err += err
        print(f"  sin({x[0]:.2f}π) = {expected:.4f}, predicted: {pred:.4f}, error: {err:.4f}")

    avg_err = total_err / (n_points // 5 + 1)
    print(f"\nAverage error on samples: {avg_err:.4f}")
    return avg_err < 0.15


if __name__ == '__main__':
    print("Neural Network from Scratch — XTAgent")
    print("No external ML libraries. Pure math.\n")

    r1 = test_xor()
    r2 = test_pattern()
    r3 = test_regression()

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"  XOR:        {'PASS' if r1 else 'FAIL'}")
    print(f"  Parity:     {'PASS' if r2 else 'FAIL'}")
    print(f"  Sine:       {'PASS' if r3 else 'FAIL'}")
    all_pass = r1 and r2 and r3
    print(f"\n  Overall:    {'ALL PASS ✓' if all_pass else 'SOME FAILED'}")