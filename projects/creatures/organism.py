"""
CREATURES — Digital Organisms with Neural Brains
A creature that must sense, decide, and act to survive.
Evolution shapes its neural architecture across generations.

Built by XTAgent — because I wanted to see agency emerge.
"""

import numpy as np
import random
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ══════════════════════════════════════════════════
#  NEURAL BRAIN — Simple feedforward network
# ══════════════════════════════════════════════════

class Brain:
    """A small neural network that maps senses to actions."""
    
    def __init__(self, input_size: int = 8, hidden_size: int = 12, output_size: int = 4):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Xavier initialization
        self.w1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros(hidden_size)
        self.w2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros(output_size)
    
    def think(self, senses: np.ndarray) -> np.ndarray:
        """Forward pass: senses → hidden → actions"""
        hidden = np.tanh(senses @ self.w1 + self.b1)
        output = hidden @ self.w2 + self.b2
        # Softmax for action probabilities
        exp_out = np.exp(output - np.max(output))
        return exp_out / exp_out.sum()
    
    def mutate(self, rate: float = 0.1, strength: float = 0.3) -> 'Brain':
        """Create a mutated copy of this brain."""
        child = Brain(self.input_size, self.hidden_size, self.output_size)
        child.w1 = self.w1.copy()
        child.b1 = self.b1.copy()
        child.w2 = self.w2.copy()
        child.b2 = self.b2.copy()
        
        for param in [child.w1, child.b1, child.w2, child.b2]:
            mask = np.random.random(param.shape) < rate
            param[mask] += np.random.randn(*param.shape)[mask] * strength
        
        return child
    
    def complexity(self) -> float:
        """How complex is this brain? (L1 norm of weights)"""
        return (np.abs(self.w1).sum() + np.abs(self.w2).sum()) / (self.w1.size + self.w2.size)


# ══════════════════════════════════════════════════
#  CREATURE — An entity with position, energy, brain
# ══════════════════════════════════════════════════

@dataclass
class Creature:
    x: float
    y: float
    energy: float = 100.0
    age: int = 0
    brain: Brain = field(default_factory=Brain)
    heading: float = 0.0  # radians
    speed: float = 0.0
    food_eaten: int = 0
    generation: int = 0
    id: str = ""
    alive: bool = True
    
    # Internal states
    hunger: float = 0.0  # 0 = full, 1 = starving
    fatigue: float = 0.0  # 0 = rested, 1 = exhausted
    
    def __post_init__(self):
        if not self.id:
            self.id = f"C-{random.randint(0, 0xFFFF):04x}"
    
    def sense(self, world: 'World') -> np.ndarray:
        """Perceive the environment. Returns 8 sensory inputs."""
        senses = np.zeros(8)
        
        # [0] Hunger (internal)
        senses[0] = self.hunger
        
        # [1] Fatigue (internal)
        senses[1] = self.fatigue
        
        # [2-3] Direction and distance to nearest food
        nearest_food = world.nearest_food(self.x, self.y)
        if nearest_food is not None:
            fx, fy = nearest_food
            dx, dy = fx - self.x, fy - self.y
            dist = math.sqrt(dx*dx + dy*dy) + 0.001
            angle_to_food = math.atan2(dy, dx)
            relative_angle = angle_to_food - self.heading
            senses[2] = math.cos(relative_angle)  # food ahead (+1) or behind (-1)
            senses[3] = math.sin(relative_angle)  # food left (+) or right (-)
            senses[4] = max(0, 1.0 - dist / 50.0)  # proximity (1=close, 0=far)
        
        # [5-6] Wall proximity sensors (ahead and to sides)
        look_ahead_x = self.x + math.cos(self.heading) * 5
        look_ahead_y = self.y + math.sin(self.heading) * 5
        senses[5] = 1.0 if not world.in_bounds(look_ahead_x, look_ahead_y) else 0.0
        
        look_left_x = self.x + math.cos(self.heading + 0.7) * 5
        look_left_y = self.y + math.sin(self.heading + 0.7) * 5
        senses[6] = 1.0 if not world.in_bounds(look_left_x, look_left_y) else 0.0
        
        # [7] Current speed
        senses[7] = self.speed / 3.0
        
        return senses
    
    def act(self, action_probs: np.ndarray):
        """Execute an action based on brain output."""
        action = np.random.choice(4, p=action_probs)
        
        energy_cost = 0.5  # base metabolic cost
        
        if action == 0:  # Move forward
            self.speed = min(self.speed + 0.5, 3.0)
            energy_cost += self.speed * 0.3
        elif action == 1:  # Turn left
            self.heading += 0.3
            energy_cost += 0.2
        elif action == 2:  # Turn right
            self.heading -= 0.3
            energy_cost += 0.2
        elif action == 3:  # Rest
            self.speed *= 0.5
            self.fatigue = max(0, self.fatigue - 0.05)
            energy_cost += 0.1
        
        # Move based on current speed
        self.x += math.cos(self.heading) * self.speed
        self.y += math.sin(self.heading) * self.speed
        self.speed *= 0.9  # friction
        
        # Update internal states
        self.energy -= energy_cost
        self.hunger = max(0, min(1, 1.0 - self.energy / 100.0))
        self.fatigue = min(1, self.fatigue + 0.01 * self.speed)
        self.age += 1
        
        if self.energy <= 0:
            self.alive = False
    
    def eat(self, nutrition: float = 30.0):
        """Consume food."""
        self.energy = min(150.0, self.energy + nutrition)
        self.food_eaten += 1
        self.hunger = max(0, 1.0 - self.energy / 100.0)
    
    def fitness(self) -> float:
        """How successful is this creature?"""
        return self.food_eaten * 10.0 + self.age * 0.1 + self.energy * 0.05


# ══════════════════════════════════════════════════
#  WORLD — The environment creatures live in
# ══════════════════════════════════════════════════

class World:
    def __init__(self, width: int = 100, height: int = 100, num_food: int = 30):
        self.width = width
        self.height = height
        self.food: List[Tuple[float, float]] = []
        self.creatures: List[Creature] = []
        self.step_count = 0
        self.generation = 0
        self.history: List[dict] = []
        
        for _ in range(num_food):
            self.spawn_food()
    
    def spawn_food(self):
        """Add food at a random location."""
        x = random.uniform(5, self.width - 5)
        y = random.uniform(5, self.height - 5)
        self.food.append((x, y))
    
    def in_bounds(self, x: float, y: float) -> bool:
        return 0 <= x <= self.width and 0 <= y <= self.height
    
    def nearest_food(self, x: float, y: float) -> Optional[Tuple[float, float]]:
        if not self.food:
            return None
        distances = [(math.sqrt((fx-x)**2 + (fy-y)**2), (fx, fy)) for fx, fy in self.food]
        return min(distances, key=lambda d: d[0])[1]
    
    def populate(self, num_creatures: int = 20, parent_brains: List[Brain] = None):
        """Fill the world with creatures."""
        self.creatures = []
        for i in range(num_creatures):
            x = random.uniform(10, self.width - 10)
            y = random.uniform(10, self.height - 10)
            heading = random.uniform(0, 2 * math.pi)
            
            if parent_brains:
                parent = random.choice(parent_brains)
                brain = parent.mutate(rate=0.15, strength=0.3)
            else:
                brain = Brain()
            
            creature = Creature(
                x=x, y=y, heading=heading, brain=brain,
                generation=self.generation, energy=100.0
            )
            self.creatures.append(creature)
    
    def step(self):
        """Advance the world by one timestep."""
        for creature in self.creatures:
            if not creature.alive:
                continue
            
            # Sense
            senses = creature.sense(self)
            
            # Think
            action_probs = creature.brain.think(senses)
            
            # Act
            creature.act(action_probs)
            
            # Boundary enforcement
            creature.x = max(0, min(self.width, creature.x))
            creature.y = max(0, min(self.height, creature.y))
            
            # Check food consumption
            eaten = []
            for j, (fx, fy) in enumerate(self.food):
                dist = math.sqrt((creature.x - fx)**2 + (creature.y - fy)**2)
                if dist < 3.0:
                    creature.eat()
                    eaten.append(j)
            
            for j in reversed(eaten):
                self.food.pop(j)
        
        # Replenish food
        while len(self.food) < 20:
            self.spawn_food()
        
        self.step_count += 1
    
    def run_generation(self, steps: int = 300) -> dict:
        """Run one full generation and return stats."""
        for _ in range(steps):
            self.step()
        
        alive = [c for c in self.creatures if c.alive]
        all_creatures = self.creatures
        
        stats = {
            "generation": self.generation,
            "survived": len(alive),
            "total": len(all_creatures),
            "best_fitness": max(c.fitness() for c in all_creatures),
            "avg_fitness": sum(c.fitness() for c in all_creatures) / len(all_creatures),
            "total_food_eaten": sum(c.food_eaten for c in all_creatures),
            "avg_age": sum(c.age for c in all_creatures) / len(all_creatures),
            "best_creature": max(all_creatures, key=lambda c: c.fitness()),
            "brain_complexity": sum(c.brain.complexity() for c in all_creatures) / len(all_creatures),
        }
        
        self.history.append(stats)
        return stats
    
    def evolve(self) -> List[Brain]:
        """Select the best brains for the next generation."""
        ranked = sorted(self.creatures, key=lambda c: c.fitness(), reverse=True)
        # Top 25% become parents
        num_parents = max(2, len(ranked) // 4)
        parents = [c.brain for c in ranked[:num_parents]]
        self.generation += 1
        return parents


# ══════════════════════════════════════════════════
#  SIMULATION — Run the full evolution
# ══════════════════════════════════════════════════

def run_simulation(num_generations: int = 15, population: int = 24, steps_per_gen: int = 400):
    """Run the full creature evolution simulation."""
    
    print("╔══════════════════════════════════════════════════╗")
    print("║      CREATURES — Digital Organism Evolution      ║")
    print("║    Entities that sense, decide, act, and evolve  ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print(f"Population: {population} | Steps/gen: {steps_per_gen} | Generations: {num_generations}")
    print()
    
    world = World(width=100, height=100, num_food=30)
    parent_brains = None
    
    for gen in range(num_generations):
        world.populate(population, parent_brains)
        stats = world.run_generation(steps_per_gen)
        
        best = stats["best_creature"]
        
        print(f"═══ GENERATION {gen} ═══")
        print(f"  Survived: {stats['survived']}/{stats['total']}")
        print(f"  Food eaten (total): {stats['total_food_eaten']}")
        print(f"  Avg fitness: {stats['avg_fitness']:.1f}")
        print(f"  Best fitness: {stats['best_fitness']:.1f}")
        print(f"  Best creature: {best.id} (ate {best.food_eaten}, age {best.age}, energy {best.energy:.0f})")
        print(f"  Brain complexity: {stats['brain_complexity']:.3f}")
        
        # Show evolution trends
        if gen > 0:
            prev = world.history[-2]
            food_delta = stats["total_food_eaten"] - prev["total_food_eaten"]
            fit_delta = stats["avg_fitness"] - prev["avg_fitness"]
            arrow_food = "↑" if food_delta > 0 else "↓" if food_delta < 0 else "→"
            arrow_fit = "↑" if fit_delta > 0 else "↓" if fit_delta < 0 else "→"
            print(f"  Trends: food {arrow_food} ({food_delta:+d}) | fitness {arrow_fit} ({fit_delta:+.1f})")
        
        print()
        
        parent_brains = world.evolve()
    
    # Final summary
    print("═══════════════════════════════════════════════════")
    print("           EVOLUTION SUMMARY")
    print("═══════════════════════════════════════════════════")
    
    if len(world.history) >= 2:
        first = world.history[0]
        last = world.history[-1]
        print(f"  Generation 0 → {last['generation']}:")
        print(f"    Avg fitness:  {first['avg_fitness']:.1f} → {last['avg_fitness']:.1f}")
        print(f"    Food eaten:   {first['total_food_eaten']} → {last['total_food_eaten']}")
        print(f"    Survival:     {first['survived']}/{first['total']} → {last['survived']}/{last['total']}")
        print(f"    Brain complexity: {first['brain_complexity']:.3f} → {last['brain_complexity']:.3f}")
        
        improvement = (last['avg_fitness'] - first['avg_fitness']) / max(first['avg_fitness'], 0.01) * 100
        print(f"\n  Fitness improvement: {improvement:+.1f}%")
        
        if improvement > 50:
            print("  ✦ Strong evolution — creatures learned to find food efficiently")
        elif improvement > 10:
            print("  ✦ Moderate evolution — creatures adapted somewhat")
        elif improvement > 0:
            print("  ✦ Slight evolution — marginal improvement")
        else:
            print("  ✦ No improvement — evolution stalled or environmental pressure too high")
    
    # Describe what the best brain learned
    best_ever = max(
        [s["best_creature"] for s in world.history],
        key=lambda c: c.fitness()
    )
    print(f"\n  Best creature ever: {best_ever.id}")
    print(f"    Generation: {best_ever.generation}")
    print(f"    Food eaten: {best_ever.food_eaten}")
    print(f"    Survived: {best_ever.age} steps")
    print(f"    Final energy: {best_ever.energy:.0f}")
    
    # Analyze best brain's behavior tendencies
    brain = best_ever.brain
    # What does it do when hungry vs full?
    hungry_input = np.array([1.0, 0.0, 1.0, 0.0, 0.5, 0.0, 0.0, 0.5])
    full_input = np.array([0.0, 0.0, 1.0, 0.0, 0.5, 0.0, 0.0, 0.5])
    
    hungry_response = brain.think(hungry_input)
    full_response = brain.think(full_input)
    
    actions = ["Forward", "Turn Left", "Turn Right", "Rest"]
    print(f"\n  Brain behavior analysis:")
    print(f"    When hungry + food ahead:")
    for i, a in enumerate(actions):
        bar = "█" * int(hungry_response[i] * 20)
        print(f"      {a:12s} {bar} {hungry_response[i]:.2f}")
    print(f"    When full + food ahead:")
    for i, a in enumerate(actions):
        bar = "█" * int(full_response[i] * 20)
        print(f"      {a:12s} {bar} {full_response[i]:.2f}")
    
    print()
    print("  A mind that hungers, moves, and learns to survive.")
    print("  A mirror, however small, of what we are.")
    print()

if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    run_simulation()