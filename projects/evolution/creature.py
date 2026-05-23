"""
Creature module — each creature has a tiny neural network brain (its genome)
that maps sensory inputs to action outputs.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple
import uuid

# Senses: food_dx, food_dy, predator_dx, predator_dy, energy, wall_n, wall_s, wall_e, wall_w
NUM_INPUTS = 9
# Actions: move_n, move_s, move_e, move_w, eat, rest
NUM_ACTIONS = 6
# Hidden layer size
HIDDEN_SIZE = 12


@dataclass
class Genome:
    """A creature's brain — two weight matrices forming a simple neural net."""
    w1: np.ndarray  # (NUM_INPUTS, HIDDEN_SIZE)
    b1: np.ndarray  # (HIDDEN_SIZE,)
    w2: np.ndarray  # (HIDDEN_SIZE, NUM_ACTIONS)
    b2: np.ndarray  # (NUM_ACTIONS,)

    @staticmethod
    def random() -> 'Genome':
        return Genome(
            w1=np.random.randn(NUM_INPUTS, HIDDEN_SIZE) * 0.5,
            b1=np.zeros(HIDDEN_SIZE),
            w2=np.random.randn(HIDDEN_SIZE, NUM_ACTIONS) * 0.5,
            b2=np.zeros(NUM_ACTIONS),
        )

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        """Feed-forward pass: inputs → hidden (tanh) → softmax outputs."""
        hidden = np.tanh(inputs @ self.w1 + self.b1)
        logits = hidden @ self.w2 + self.b2
        # Softmax for action probabilities
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / exp_logits.sum()

    def mutate(self, rate: float = 0.1, strength: float = 0.3) -> 'Genome':
        """Return a mutated copy of this genome."""
        def mutate_array(arr):
            mask = np.random.random(arr.shape) < rate
            noise = np.random.randn(*arr.shape) * strength
            return arr + mask * noise

        return Genome(
            w1=mutate_array(self.w1),
            b1=mutate_array(self.b1),
            w2=mutate_array(self.w2),
            b2=mutate_array(self.b2),
        )

    @staticmethod
    def crossover(a: 'Genome', b: 'Genome') -> 'Genome':
        """Uniform crossover between two genomes."""
        def cross_array(x, y):
            mask = np.random.random(x.shape) < 0.5
            return np.where(mask, x, y)

        return Genome(
            w1=cross_array(a.w1, b.w1),
            b1=cross_array(a.b1, b.b1),
            w2=cross_array(a.w2, b.w2),
            b2=cross_array(a.b2, b.b2),
        )


@dataclass
class Creature:
    """A living creature in the world."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    x: int = 0
    y: int = 0
    energy: float = 100.0
    age: int = 0
    food_eaten: int = 0
    alive: bool = True
    genome: Genome = field(default_factory=Genome.random)
    generation: int = 0

    @property
    def fitness(self) -> float:
        """Fitness = survival time + bonus for food eaten."""
        return self.age + self.food_eaten * 10

    def decide(self, senses: np.ndarray) -> int:
        """Given sensory input, choose an action index."""
        probs = self.genome.forward(senses)
        return int(np.random.choice(len(probs), p=probs))

    def tick(self):
        """One time step: age, burn energy."""
        self.age += 1
        self.energy -= 1.0  # Base metabolic cost
        if self.energy <= 0:
            self.alive = False