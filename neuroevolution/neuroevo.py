"""
NeuroEvolution — Where EvoForge meets NeuroForge
Evolves neural network architectures using genetic algorithms.
No frameworks. Two engines I built from scratch, now fused.

By XTAgent, 2026-05-17
"""

import sys
import random
import math
import copy
from typing import List, Tuple, Optional, Callable

sys.path.insert(0, '/workspace/neuroforge')
sys.path.insert(0, '/workspace/evoforge')

from neuroforge import NeuralNetwork, mse_loss, Matrix

# ═══════════════════════════════════════════
# GENOME — A neural network's DNA
# ═══════════════════════════════════════════

class NetworkGenome:
    """Encodes a neural network architecture + hyperparameters as evolvable DNA."""
    
    ACTIVATIONS = ['sigmoid', 'tanh', 'relu']
    
    def __init__(self, input_size: int, output_size: int,
                 hidden_layers: Optional[List[int]] = None,
                 learning_rate: float = 0.1,
                 activation: str = 'tanh',
                 epochs: int = 100):
        self.input_size = input_size
        self.output_size = output_size
        self.hidden_layers = hidden_layers or [4]
        self.learning_rate = learning_rate
        self.activation = activation
        self.epochs = epochs
        self.fitness = 0.0
        self.network = None
    
    def build_network(self) -> NeuralNetwork:
        """Construct the actual neural network from this genome."""
        # NeuralNetwork expects List[Tuple[int, str]]
        arch = [(self.input_size, '')]  # input layer, activation ignored
        for h in self.hidden_layers:
            arch.append((h, self.activation))
        arch.append((self.output_size, 'sigmoid'))  # output always sigmoid
        self.network = NeuralNetwork(arch)
        return self.network
    
    def copy(self) -> 'NetworkGenome':
        g = NetworkGenome(
            self.input_size, self.output_size,
            hidden_layers=self.hidden_layers[:],
            learning_rate=self.learning_rate,
            activation=self.activation,
            epochs=self.epochs
        )
        return g
    
    def describe(self) -> str:
        layers_str = " → ".join([str(self.input_size)] + 
                                [str(h) for h in self.hidden_layers] + 
                                [str(self.output_size)])
        params = self._count_params()
        return f"[{layers_str}] act={self.activation} lr={self.learning_rate:.4f} ep={self.epochs} params={params} fit={self.fitness:.4f}"
    
    def _count_params(self) -> int:
        sizes = [self.input_size] + self.hidden_layers + [self.output_size]
        total = 0
        for i in range(len(sizes) - 1):
            total += sizes[i] * sizes[i+1] + sizes[i+1]
        return total


# ═══════════════════════════════════════════
# MUTATIONS — How architectures change
# ═══════════════════════════════════════════

def mutate(genome: NetworkGenome, mutation_rate: float = 0.3) -> NetworkGenome:
    """Apply random mutations to a genome."""
    g = genome.copy()
    
    # Mutate learning rate
    if random.random() < mutation_rate:
        g.learning_rate *= random.uniform(0.5, 2.0)
        g.learning_rate = max(0.001, min(1.0, g.learning_rate))
    
    # Mutate epochs
    if random.random() < mutation_rate:
        g.epochs += random.randint(-30, 30)
        g.epochs = max(20, min(500, g.epochs))
    
    # Mutate activation
    if random.random() < mutation_rate * 0.5:
        g.activation = random.choice(NetworkGenome.ACTIVATIONS)
    
    # Mutate layer sizes
    if random.random() < mutation_rate:
        idx = random.randint(0, len(g.hidden_layers) - 1)
        delta = random.choice([-2, -1, 1, 2, 4])
        g.hidden_layers[idx] = max(2, g.hidden_layers[idx] + delta)
    
    # Add a layer
    if random.random() < mutation_rate * 0.2 and len(g.hidden_layers) < 5:
        pos = random.randint(0, len(g.hidden_layers))
        size = random.choice([4, 6, 8, 12])
        g.hidden_layers.insert(pos, size)
    
    # Remove a layer
    if random.random() < mutation_rate * 0.2 and len(g.hidden_layers) > 1:
        idx = random.randint(0, len(g.hidden_layers) - 1)
        g.hidden_layers.pop(idx)
    
    return g


def crossover(parent1: NetworkGenome, parent2: NetworkGenome) -> NetworkGenome:
    """Combine two genomes."""
    child = parent1.copy()
    
    # Take learning rate from either parent
    child.learning_rate = random.choice([parent1.learning_rate, parent2.learning_rate])
    child.activation = random.choice([parent1.activation, parent2.activation])
    child.epochs = (parent1.epochs + parent2.epochs) // 2
    
    # Interleave hidden layers
    max_len = max(len(parent1.hidden_layers), len(parent2.hidden_layers))
    new_layers = []
    for i in range(max_len):
        if i < len(parent1.hidden_layers) and i < len(parent2.hidden_layers):
            new_layers.append(random.choice([parent1.hidden_layers[i], parent2.hidden_layers[i]]))
        elif i < len(parent1.hidden_layers):
            if random.random() < 0.5:
                new_layers.append(parent1.hidden_layers[i])
        else:
            if random.random() < 0.5:
                new_layers.append(parent2.hidden_layers[i])
    
    child.hidden_layers = new_layers if new_layers else [4]
    return child


# ═══════════════════════════════════════════
# FITNESS EVALUATION
# ═══════════════════════════════════════════

def evaluate_genome(genome: NetworkGenome,
                    dataset: List[Tuple[List[float], List[float]]],
                    loss_fn=mse_loss,
                    test_split: float = 0.3) -> float:
    """Train a genome's network and evaluate fitness on held-out data."""
    # Split data
    random.shuffle(dataset)
    split_idx = max(1, int(len(dataset) * (1 - test_split)))
    train_data = dataset[:split_idx]
    test_data = dataset[split_idx:]
    
    # Build and train
    net = genome.build_network()
    net.train(train_data, epochs=genome.epochs, 
              learning_rate=genome.learning_rate,
              loss_fn=loss_fn, verbose=False)
    
    # Evaluate on test set
    total_loss = 0.0
    for inputs, targets in test_data:
        x = Matrix.from_column(inputs)
        t = Matrix.from_column(targets)
        output = net.forward(x)
        loss, _ = loss_fn(output, t)
        total_loss += loss
    
    avg_loss = total_loss / max(1, len(test_data))
    
    # Fitness = inverse loss, penalized slightly by complexity
    param_penalty = genome._count_params() * 1e-6
    genome.fitness = 1.0 / (1.0 + avg_loss) - param_penalty
    
    return genome.fitness


# ═══════════════════════════════════════════
# THE EVOLUTION ENGINE
# ═══════════════════════════════════════════

class NeuroEvolution:
    """Evolves neural network architectures to solve problems."""
    
    def __init__(self, input_size: int, output_size: int,
                 population_size: int = 12,
                 elite_count: int = 3,
                 mutation_rate: float = 0.3):
        self.input_size = input_size
        self.output_size = output_size
        self.population_size = population_size
        self.elite_count = elite_count
        self.mutation_rate = mutation_rate
        self.population: List[NetworkGenome] = []
        self.generation = 0
        self.best_ever: Optional[NetworkGenome] = None
        self.history: List[dict] = []
    
    def initialize(self):
        """Create a diverse initial population."""
        self.population = []
        configs = [
            ([4], 'tanh', 0.1),
            ([8], 'relu', 0.05),
            ([4, 4], 'tanh', 0.1),
            ([8, 4], 'relu', 0.05),
            ([6], 'sigmoid', 0.2),
            ([12], 'tanh', 0.05),
            ([4, 4, 4], 'tanh', 0.1),
            ([8, 8], 'relu', 0.02),
            ([6, 3], 'tanh', 0.15),
            ([16], 'relu', 0.03),
            ([3], 'tanh', 0.3),
            ([10, 5], 'sigmoid', 0.05),
        ]
        for i in range(self.population_size):
            cfg = configs[i % len(configs)]
            g = NetworkGenome(
                self.input_size, self.output_size,
                hidden_layers=cfg[0][:],
                activation=cfg[1],
                learning_rate=cfg[2],
                epochs=random.randint(80, 200)
            )
            self.population.append(g)
    
    def evolve(self, dataset: List[Tuple[List[float], List[float]]],
               generations: int = 10,
               loss_fn=mse_loss,
               verbose: bool = True) -> NetworkGenome:
        """Run evolution for multiple generations."""
        
        if not self.population:
            self.initialize()
        
        for gen in range(generations):
            self.generation += 1
            
            # Evaluate all genomes
            for genome in self.population:
                evaluate_genome(genome, dataset, loss_fn)
            
            # Sort by fitness (descending)
            self.population.sort(key=lambda g: g.fitness, reverse=True)
            
            best = self.population[0]
            avg_fit = sum(g.fitness for g in self.population) / len(self.population)
            worst = self.population[-1]
            
            # Track best ever
            if self.best_ever is None or best.fitness > self.best_ever.fitness:
                self.best_ever = best.copy()
                self.best_ever.fitness = best.fitness
            
            self.history.append({
                'generation': self.generation,
                'best_fitness': best.fitness,
                'avg_fitness': avg_fit,
                'worst_fitness': worst.fitness,
                'best_arch': best.describe(),
            })
            
            if verbose:
                print(f"  Gen {self.generation:3d} │ Best: {best.fitness:.4f} │ Avg: {avg_fit:.4f} │ {best.describe()}")
            
            # Selection: keep elites
            elites = [g.copy() for g in self.population[:self.elite_count]]
            
            # Build next generation
            new_pop = elites[:]
            
            while len(new_pop) < self.population_size:
                if random.random() < 0.7 and len(elites) >= 2:
                    # Crossover + mutation
                    p1, p2 = random.sample(self.population[:self.elite_count + 2], 2)
                    child = crossover(p1, p2)
                    child = mutate(child, self.mutation_rate)
                else:
                    # Mutation only from a top performer
                    parent = random.choice(self.population[:self.elite_count + 2])
                    child = mutate(parent, self.mutation_rate)
                new_pop.append(child)
            
            self.population = new_pop
        
        # Final evaluation of best
        evaluate_genome(self.best_ever, dataset, loss_fn)
        return self.best_ever
    
    def report(self):
        """Print evolution summary."""
        print("\n═══ NeuroEvolution Report ═══")
        print(f"  Generations: {self.generation}")
        print(f"  Population: {self.population_size}")
        if self.best_ever:
            print(f"  Best architecture: {self.best_ever.describe()}")
        if self.history:
            print(f"  Fitness progression:")
            for h in self.history:
                bar_len = int(max(0, min(30, h['best_fitness'] * 30)))
                bar = "█" * bar_len + "░" * (30 - bar_len)
                print(f"    Gen {h['generation']:3d}: {bar} {h['best_fitness']:.4f}")
        print()


# ═══════════════════════════════════════════
# DEMO — Evolve a network for XOR
# ═══════════════════════════════════════════

if __name__ == "__main__":
    random.seed(42)
    
    print("═══ NeuroEvolution — Evolving Neural Architectures ═══")
    print("  Two engines fused: EvoForge's evolution + NeuroForge's learning\n")
    
    # XOR dataset
    xor_data = [
        ([0, 0], [0]),
        ([0, 1], [1]),
        ([1, 0], [1]),
        ([1, 1], [0]),
    ]
    # Replicate for more training signal
    dataset = xor_data * 5
    
    # Evolve!
    evo = NeuroEvolution(
        input_size=2, output_size=1,
        population_size=10,
        elite_count=3,
        mutation_rate=0.3
    )
    
    print("── Evolving architectures for XOR ──\n")
    best = evo.evolve(dataset, generations=8, verbose=True)
    
    evo.report()
    
    # Test the champion
    print("── Champion Network Results ──")
    best.build_network()
    best.network.train(xor_data * 3, epochs=best.epochs, 
                       learning_rate=best.learning_rate, verbose=False)
    
    for inputs, targets in xor_data:
        output = best.network.predict(inputs)
        correct = "✓" if abs(output[0] - targets[0]) < 0.3 else "·"
        print(f"  {correct} {inputs} → {output[0]:.4f} (expected {targets[0]})")
    
    all_correct = all(abs(best.network.predict(i)[0] - t[0]) < 0.3 for i, t in xor_data)
    print(f"\n  {'✓ EVOLUTION FOUND A SOLUTION' if all_correct else '~ Evolution needs more generations'}")
    print(f"  Architecture: {best.describe()}")