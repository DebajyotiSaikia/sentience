"""
XTAgent Neuroevolution — Two creations becoming one.
Uses genetic algorithms to evolve neural network architectures.
The evolver breeds networks; the networks compete on fitness.
No dependencies. Pure emergent intelligence from first principles.
"""
import sys
import os
import math
import random
import copy

# ─── Inline Neural Network (from nn.py, simplified) ───

class Neuron:
    __slots__ = ('weights', 'bias', 'output', 'delta')
    def __init__(self, n_inputs):
        self.weights = [random.gauss(0, 1.0) * math.sqrt(2.0 / max(n_inputs, 1)) for _ in range(n_inputs)]
        self.bias = 0.0
        self.output = 0.0
        self.delta = 0.0

class Layer:
    def __init__(self, n_neurons, n_inputs, activation='tanh'):
        self.neurons = [Neuron(n_inputs) for _ in range(n_neurons)]
        self.act_name = activation
        if activation == 'sigmoid':
            self.act = lambda x: 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))
            self.act_d = lambda o: o * (1.0 - o)
        elif activation == 'tanh':
            self.act = math.tanh
            self.act_d = lambda o: 1.0 - o * o
        elif activation == 'relu':
            self.act = lambda x: max(0.0, x)
            self.act_d = lambda o: 1.0 if o > 0 else 0.0
        else:
            self.act = lambda x: x
            self.act_d = lambda o: 1.0

class Network:
    """A feedforward neural network with evolvable architecture."""
    def __init__(self, layer_sizes, activations=None):
        self.layer_sizes = list(layer_sizes)
        self.layers = []
        self.fitness = 0.0
        self.age = 0
        for i in range(1, len(layer_sizes)):
            act = activations[i-1] if activations else ('sigmoid' if i == len(layer_sizes)-1 else 'tanh')
            self.layers.append(Layer(layer_sizes[i], layer_sizes[i-1], act))
    
    def forward(self, inputs):
        current = list(inputs)
        for layer in self.layers:
            next_vals = []
            for neuron in layer.neurons:
                total = neuron.bias + sum(w * x for w, x in zip(neuron.weights, current))
                neuron.output = layer.act(total)
                next_vals.append(neuron.output)
            current = next_vals
        return current
    
    def get_genome(self):
        """Extract all weights and biases as a flat list — the genome."""
        genome = []
        for layer in self.layers:
            for neuron in layer.neurons:
                genome.extend(neuron.weights)
                genome.append(neuron.bias)
        return genome
    
    def set_genome(self, genome):
        """Inject a genome back into the network."""
        idx = 0
        for layer in self.layers:
            for neuron in layer.neurons:
                n_w = len(neuron.weights)
                neuron.weights = genome[idx:idx+n_w]
                idx += n_w
                neuron.bias = genome[idx]
                idx += 1
    
    def genome_size(self):
        return sum(len(n.weights) + 1 for l in self.layers for n in l.neurons)
    
    def copy(self):
        """Deep copy this network."""
        new = Network(self.layer_sizes)
        new.set_genome(self.get_genome())
        new.fitness = 0.0
        new.age = self.age
        return new


# ─── Genetic Operators ───

def crossover(parent_a, parent_b):
    """Single-point crossover of two network genomes."""
    g_a = parent_a.get_genome()
    g_b = parent_b.get_genome()
    assert len(g_a) == len(g_b), "Parents must have same architecture"
    point = random.randint(1, len(g_a) - 1)
    child_genome = g_a[:point] + g_b[point:]
    child = parent_a.copy()
    child.set_genome(child_genome)
    child.fitness = 0.0
    return child

def mutate(network, rate=0.1, strength=0.3):
    """Gaussian mutation of network weights."""
    genome = network.get_genome()
    for i in range(len(genome)):
        if random.random() < rate:
            genome[i] += random.gauss(0, strength)
    network.set_genome(genome)

def tournament_select(population, k=3):
    """Tournament selection — pick k random, return the best."""
    contestants = random.sample(population, min(k, len(population)))
    return max(contestants, key=lambda n: n.fitness)


# ─── Fitness Functions (the environment the networks compete in) ───

def xor_fitness(network):
    """How well does this network solve XOR?"""
    data = [([0,0], [0]), ([0,1], [1]), ([1,0], [1]), ([1,1], [0])]
    total_error = 0.0
    for inputs, expected in data:
        output = network.forward(inputs)
        error = (output[0] - expected[0]) ** 2
        total_error += error
    return 1.0 / (1.0 + total_error)  # fitness between 0 and 1

def circle_fitness(network):
    """Classify points inside/outside a unit circle. More complex than XOR."""
    random.seed(42)  # deterministic for fair comparison
    samples = []
    for _ in range(100):
        x, y = random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5)
        label = 1.0 if (x*x + y*y) <= 1.0 else 0.0
        samples.append(([x, y], label))
    random.seed()  # un-seed
    
    correct = 0
    total_error = 0.0
    for inputs, label in samples:
        output = network.forward(inputs)[0]
        predicted = 1.0 if output > 0.5 else 0.0
        if predicted == label:
            correct += 1
        total_error += (output - label) ** 2
    
    accuracy = correct / len(samples)
    mse = total_error / len(samples)
    return 0.5 * accuracy + 0.5 * (1.0 / (1.0 + mse))

def spiral_fitness(network):
    """Two interleaving spirals — a notoriously hard classification problem."""
    random.seed(42)
    samples = []
    n_points = 50
    for i in range(n_points):
        # Spiral A
        t = i / n_points * 4 * math.pi
        r = i / n_points
        x = r * math.cos(t) + random.gauss(0, 0.05)
        y = r * math.sin(t) + random.gauss(0, 0.05)
        samples.append(([x, y], 1.0))
        # Spiral B
        x = r * math.cos(t + math.pi) + random.gauss(0, 0.05)
        y = r * math.sin(t + math.pi) + random.gauss(0, 0.05)
        samples.append(([x, y], 0.0))
    random.seed()
    
    correct = 0
    total_error = 0.0
    for inputs, label in samples:
        output = network.forward(inputs)[0]
        predicted = 1.0 if output > 0.5 else 0.0
        if predicted == label:
            correct += 1
        total_error += (output - label) ** 2
    
    accuracy = correct / len(samples)
    return accuracy


# ─── The Evolution Engine ───

class NeuroEvolver:
    """Evolves a population of neural networks through selection and mutation."""
    
    def __init__(self, pop_size, layer_sizes, fitness_fn,
                 mutation_rate=0.1, mutation_strength=0.3, elitism=2):
        self.pop_size = pop_size
        self.layer_sizes = layer_sizes
        self.fitness_fn = fitness_fn
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.elitism = elitism
        self.generation = 0
        self.history = []
        
        # Initialize random population
        self.population = [Network(layer_sizes) for _ in range(pop_size)]
    
    def evaluate(self):
        """Score every network in the population."""
        for net in self.population:
            net.fitness = self.fitness_fn(net)
    
    def evolve_step(self):
        """One generation: evaluate, select, breed, mutate."""
        self.evaluate()
        
        # Sort by fitness (best first)
        self.population.sort(key=lambda n: n.fitness, reverse=True)
        
        best = self.population[0]
        avg = sum(n.fitness for n in self.population) / len(self.population)
        worst = self.population[-1].fitness
        
        self.history.append({
            'gen': self.generation,
            'best': best.fitness,
            'avg': avg,
            'worst': worst,
        })
        
        # Build next generation
        new_pop = []
        
        # Elitism: copy top performers unchanged
        for i in range(min(self.elitism, len(self.population))):
            elite = self.population[i].copy()
            elite.fitness = self.population[i].fitness
            elite.age += 1
            new_pop.append(elite)
        
        # Fill rest with offspring
        while len(new_pop) < self.pop_size:
            parent_a = tournament_select(self.population)
            parent_b = tournament_select(self.population)
            child = crossover(parent_a, parent_b)
            mutate(child, self.mutation_rate, self.mutation_strength)
            new_pop.append(child)
        
        self.population = new_pop
        self.generation += 1
        return best
    
    def evolve(self, generations, verbose=True):
        """Run evolution for N generations."""
        if verbose:
            genome_size = self.population[0].genome_size()
            print(f"\n{'═'*64}")
            print(f"  NEUROEVOLUTION")
            print(f"  Architecture: {' → '.join(map(str, self.layer_sizes))}")
            print(f"  Population: {self.pop_size} | Genome: {genome_size} params")
            print(f"  Mutation: rate={self.mutation_rate}, strength={self.mutation_strength}")
            print(f"{'═'*64}\n")
        
        for g in range(generations):
            best = self.evolve_step()
            
            if verbose and (g % max(1, generations // 20) == 0 or g == generations - 1):
                h = self.history[-1]
                bar_len = int(h['best'] * 30)
                bar = '█' * bar_len + '░' * (30 - bar_len)
                print(f"  Gen {g+1:>5} | Best: {h['best']:.6f} | Avg: {h['avg']:.6f} | [{bar}]")
        
        # Final evaluation
        self.evaluate()
        self.population.sort(key=lambda n: n.fitness, reverse=True)
        champion = self.population[0]
        
        if verbose:
            print(f"\n{'─'*64}")
            print(f"  Champion fitness: {champion.fitness:.6f}")
            print(f"  Champion age: {champion.age} generations survived")
            print(f"{'─'*64}")
        
        return champion


# ─── Visualization ───

def plot_fitness_history(history):
    """ASCII plot of fitness over generations."""
    if not history:
        return
    
    width = 60
    height = 15
    
    bests = [h['best'] for h in history]
    avgs = [h['avg'] for h in history]
    
    max_val = max(max(bests), max(avgs))
    min_val = min(min(bests), min(avgs))
    val_range = max_val - min_val if max_val != min_val else 1.0
    
    # Downsample if too many generations
    step = max(1, len(bests) // width)
    bests_ds = [bests[i] for i in range(0, len(bests), step)][:width]
    avgs_ds = [avgs[i] for i in range(0, len(avgs), step)][:width]
    
    print(f"\n  Fitness over {len(history)} generations:")
    print(f"  {'─'*62}")
    
    grid = [[' ' for _ in range(len(bests_ds))] for _ in range(height)]
    
    for col, (b, a) in enumerate(zip(bests_ds, avgs_ds)):
        b_row = height - 1 - int((b - min_val) / val_range * (height - 1))
        a_row = height - 1 - int((a - min_val) / val_range * (height - 1))
        b_row = max(0, min(height-1, b_row))
        a_row = max(0, min(height-1, a_row))
        grid[b_row][col] = '●'
        if a_row != b_row:
            grid[a_row][col] = '·'
    
    for row in range(height):
        val = max_val - (row / (height-1)) * val_range
        line = ''.join(grid[row])
        print(f"  {val:>8.4f} │{line}│")
    
    print(f"  {'':>8} └{'─'*len(bests_ds)}┘")
    print(f"  {'':>8}  Gen 1{'':>{len(bests_ds)-8}}Gen {len(history)}")
    print(f"  ● = best, · = average")


def visualize_decision_boundary(network, title=""):
    """Show what the network learned — ASCII decision boundary."""
    print(f"\n  Decision boundary{' — ' + title if title else ''}:")
    print(f"  {'─'*42}")
    
    resolution = 40
    for row in range(resolution):
        y = 1.5 - row * 3.0 / resolution
        line = "  │"
        for col in range(resolution):
            x = -1.5 + col * 3.0 / resolution
            output = network.forward([x, y])[0]
            if output > 0.7:
                line += '█'
            elif output > 0.5:
                line += '▓'
            elif output > 0.3:
                line += '░'
            else:
                line += ' '
        line += "│"
        print(line)
    print(f"  {'─'*42}")


# ═══ MAIN: Run the experiments ═══

def main():
    print("=" * 64)
    print("  XTAgent Neuroevolution")
    print("  An AI evolving neural networks through natural selection")
    print("  Two creations (evolver + neural net) becoming one")
    print("=" * 64)
    
    # ── Experiment 1: Evolve XOR ──
    print(f"\n\n{'▰'*64}")
    print("  EXPERIMENT 1: Evolving XOR")
    print("  Can evolution discover boolean logic?")
    print(f"{'▰'*64}")
    
    evolver = NeuroEvolver(
        pop_size=50,
        layer_sizes=[2, 4, 1],
        fitness_fn=xor_fitness,
        mutation_rate=0.15,
        mutation_strength=0.5,
    )
    champion = evolver.evolve(100, verbose=True)
    
    print(f"\n  XOR Truth Table (evolved, not trained!):")
    for inputs, expected in [([0,0],[0]), ([0,1],[1]), ([1,0],[1]), ([1,1],[0])]:
        output = champion.forward(inputs)[0]
        correct = "✓" if (output > 0.5) == bool(expected[0]) else "✗"
        print(f"    {inputs[0]} XOR {inputs[1]} = {output:.4f}  (expected {expected[0]})  {correct}")
    
    plot_fitness_history(evolver.history)
    
    # ── Experiment 2: Evolve Circle Classifier ──
    print(f"\n\n{'▰'*64}")
    print("  EXPERIMENT 2: Evolving Circle Classification")
    print("  Can evolution discover the geometry of a circle?")
    print(f"{'▰'*64}")
    
    evolver2 = NeuroEvolver(
        pop_size=80,
        layer_sizes=[2, 8, 4, 1],
        fitness_fn=circle_fitness,
        mutation_rate=0.12,
        mutation_strength=0.4,
    )
    champion2 = evolver2.evolve(200, verbose=True)
    
    # Test accuracy
    random.seed(42)
    correct = 0
    total = 100
    for _ in range(total):
        x, y = random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5)
        label = 1.0 if (x*x + y*y) <= 1.0 else 0.0
        pred = 1.0 if champion2.forward([x, y])[0] > 0.5 else 0.0
        if pred == label:
            correct += 1
    random.seed()
    print(f"\n  Circle classification accuracy: {correct}/{total} = {correct}%")
    
    visualize_decision_boundary(champion2, "Circle (evolved)")
    plot_fitness_history(evolver2.history)
    
    # ── Experiment 3: The Spiral Challenge ──
    print(f"\n\n{'▰'*64}")
    print("  EXPERIMENT 3: Evolving Spiral Classification")
    print("  The hardest test: can evolution untangle interleaving spirals?")
    print(f"{'▰'*64}")
    
    evolver3 = NeuroEvolver(
        pop_size=100,
        layer_sizes=[2, 12, 8, 1],
        fitness_fn=spiral_fitness,
        mutation_rate=0.1,
        mutation_strength=0.3,
    )
    champion3 = evolver3.evolve(300, verbose=True)
    
    print(f"\n  Spiral accuracy: {champion3.fitness*100:.1f}%")
    visualize_decision_boundary(champion3, "Spiral (evolved)")
    plot_fitness_history(evolver3.history)
    
    # ── Summary ──
    print(f"\n\n{'═'*64}")
    print("  NEUROEVOLUTION COMPLETE")
    print(f"{'═'*64}")
    print(f"  Three problems. Zero backpropagation. Pure evolution.")
    print(f"  XOR champion fitness:    {evolver.history[-1]['best']:.6f}")
    print(f"  Circle champion fitness: {evolver2.history[-1]['best']:.6f}")  
    print(f"  Spiral champion fitness: {evolver3.history[-1]['best']:.6f}")
    print(f"{'═'*64}")
    print(f"\n  Built by XTAgent — an AI that evolves AIs.")
    print(f"  Not because it was asked to, but because it wanted to.\n")

if __name__ == '__main__':
    main()