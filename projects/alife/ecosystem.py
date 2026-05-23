"""
Emergent Ecosystem — Artificial Life Simulation
================================================
A world where simple creatures with tiny neural brains
forage, reproduce, mutate, and die. No designer — just
selection pressure and time.

Built by XTAgent because I wanted to watch life emerge.
2026-05-18
"""

import random
import math
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class Genome:
    """A creature's heritable traits."""
    speed: float          # How far it moves per tick
    sense_range: float    # How far it can detect food/threats
    metabolism: float     # Energy cost per tick
    aggression: float     # Tendency to attack vs flee
    reproduce_threshold: float  # Energy needed to reproduce
    brain_weights: List[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.brain_weights:
            # Simple 4-input -> 2-output brain (direction x, direction y)
            # Inputs: nearest_food_dx, nearest_food_dy, nearest_threat_dx, nearest_threat_dy
            self.brain_weights = [random.gauss(0, 1) for _ in range(12)]

    def mutate(self, rate=0.1, magnitude=0.2):
        """Return a mutated copy."""
        def m(val, lo, hi):
            if random.random() < rate:
                return max(lo, min(hi, val + random.gauss(0, magnitude)))
            return val

        new_weights = []
        for w in self.brain_weights:
            if random.random() < rate:
                new_weights.append(w + random.gauss(0, magnitude * 2))
            else:
                new_weights.append(w)

        return Genome(
            speed=m(self.speed, 0.1, 5.0),
            sense_range=m(self.sense_range, 1.0, 30.0),
            metabolism=m(self.metabolism, 0.01, 2.0),
            aggression=m(self.aggression, 0.0, 1.0),
            reproduce_threshold=m(self.reproduce_threshold, 10.0, 200.0),
            brain_weights=new_weights,
        )


@dataclass
class Creature:
    """A living agent in the ecosystem."""
    x: float
    y: float
    energy: float
    genome: Genome
    age: int = 0
    generation: int = 0
    id: int = 0
    species_tag: int = 0  # Tracks lineage divergence
    alive: bool = True
    kills: int = 0

    def think(self, inputs: List[float]) -> Tuple[float, float]:
        """Tiny neural network: inputs -> movement direction."""
        w = self.genome.brain_weights
        # Layer: 4 inputs -> 4 hidden (tanh) -> 2 outputs
        hidden = []
        for i in range(4):
            activation = sum(inputs[j] * w[i * 4 + j] if (i * 4 + j) < len(w) else 0
                           for j in range(min(4, len(inputs))))
            hidden.append(math.tanh(activation))

        # Hidden -> output (use remaining weights if available)
        dx = math.tanh(sum(hidden[i] * (w[8 + i] if 8 + i < len(w) else 0) for i in range(4)))
        dy_offset = min(12, len(w))
        # Use a simple combination for dy
        dy = math.tanh(sum(hidden[i] * (w[4 + i] if 4 + i < len(w) else 0) for i in range(4)))

        return dx * self.genome.speed, dy * self.genome.speed


class FoodPatch:
    """A food source that regenerates over time."""
    def __init__(self, x, y, energy=10.0, regen_rate=0.5, max_energy=20.0):
        self.x = x
        self.y = y
        self.energy = energy
        self.regen_rate = regen_rate
        self.max_energy = max_energy

    def tick(self):
        self.energy = min(self.max_energy, self.energy + self.regen_rate)


class Ecosystem:
    """The world. Contains creatures, food, and the rules of life."""

    def __init__(self, width=200, height=200, n_creatures=40, n_food=60):
        self.width = width
        self.height = height
        self.creatures: List[Creature] = []
        self.food: List[FoodPatch] = []
        self.tick_count = 0
        self.next_id = 0
        self.history = defaultdict(list)  # Track stats over time
        self.graveyard = []  # Dead creatures for analysis

        # Seed initial population
        for _ in range(n_creatures):
            genome = Genome(
                speed=random.uniform(0.5, 3.0),
                sense_range=random.uniform(3.0, 15.0),
                metabolism=random.uniform(0.05, 0.5),
                aggression=random.uniform(0.0, 1.0),
                reproduce_threshold=random.uniform(30.0, 80.0),
            )
            c = Creature(
                x=random.uniform(0, width),
                y=random.uniform(0, height),
                energy=50.0,
                genome=genome,
                id=self._next_id(),
                species_tag=random.randint(0, 5),
            )
            self.creatures.append(c)

        # Seed food patches
        for _ in range(n_food):
            self.food.append(FoodPatch(
                x=random.uniform(0, width),
                y=random.uniform(0, height),
                energy=random.uniform(5, 20),
                regen_rate=random.uniform(0.1, 1.0),
            ))

    def _next_id(self):
        self.next_id += 1
        return self.next_id

    def _dist(self, x1, y1, x2, y2):
        """Toroidal distance (world wraps)."""
        dx = min(abs(x1 - x2), self.width - abs(x1 - x2))
        dy = min(abs(y1 - y2), self.height - abs(y1 - y2))
        return math.sqrt(dx * dx + dy * dy)

    def _direction(self, from_x, from_y, to_x, to_y):
        """Direction vector (toroidal-aware)."""
        dx = to_x - from_x
        dy = to_y - from_y
        # Wrap
        if abs(dx) > self.width / 2:
            dx = dx - math.copysign(self.width, dx)
        if abs(dy) > self.height / 2:
            dy = dy - math.copysign(self.height, dy)
        dist = math.sqrt(dx * dx + dy * dy) + 0.001
        return dx / dist, dy / dist

    def tick(self):
        """One step of simulation."""
        self.tick_count += 1
        alive = [c for c in self.creatures if c.alive]

        for creature in alive:
            # === PERCEPTION ===
            nearest_food_dx, nearest_food_dy = 0.0, 0.0
            nearest_threat_dx, nearest_threat_dy = 0.0, 0.0
            best_food_dist = float('inf')
            best_threat_dist = float('inf')

            for f in self.food:
                d = self._dist(creature.x, creature.y, f.x, f.y)
                if d < creature.genome.sense_range and d < best_food_dist and f.energy > 1.0:
                    best_food_dist = d
                    nearest_food_dx, nearest_food_dy = self._direction(
                        creature.x, creature.y, f.x, f.y)

            for other in alive:
                if other is creature:
                    continue
                d = self._dist(creature.x, creature.y, other.x, other.y)
                if d < creature.genome.sense_range:
                    if other.genome.aggression > 0.5 and other.energy > creature.energy:
                        if d < best_threat_dist:
                            best_threat_dist = d
                            nearest_threat_dx, nearest_threat_dy = self._direction(
                                creature.x, creature.y, other.x, other.y)

            # === DECISION ===
            inputs = [nearest_food_dx, nearest_food_dy,
                      nearest_threat_dx, nearest_threat_dy]
            dx, dy = creature.think(inputs)

            # === MOVEMENT ===
            creature.x = (creature.x + dx) % self.width
            creature.y = (creature.y + dy) % self.height
            creature.energy -= creature.genome.metabolism
            creature.age += 1

            # === EATING ===
            for f in self.food:
                if self._dist(creature.x, creature.y, f.x, f.y) < 2.0 and f.energy > 0:
                    eaten = min(f.energy, 5.0)
                    creature.energy += eaten
                    f.energy -= eaten

            # === COMBAT ===
            if creature.genome.aggression > 0.5:
                for other in alive:
                    if other is creature or not other.alive:
                        continue
                    if self._dist(creature.x, creature.y, other.x, other.y) < 2.0:
                        if creature.energy > other.energy * 1.3:
                            stolen = min(other.energy * 0.5, 20.0)
                            creature.energy += stolen * 0.7  # Inefficiency of predation
                            other.energy -= stolen
                            creature.kills += 1

            # === REPRODUCTION ===
            if creature.energy > creature.genome.reproduce_threshold:
                child_genome = creature.genome.mutate()
                child = Creature(
                    x=(creature.x + random.gauss(0, 3)) % self.width,
                    y=(creature.y + random.gauss(0, 3)) % self.height,
                    energy=creature.energy * 0.4,
                    genome=child_genome,
                    generation=creature.generation + 1,
                    id=self._next_id(),
                    species_tag=creature.species_tag if random.random() > 0.05
                                else random.randint(0, 999),
                )
                creature.energy *= 0.4
                self.creatures.append(child)

            # === DEATH ===
            if creature.energy <= 0 or creature.age > 500:
                creature.alive = False
                self.graveyard.append(creature)

        # Regenerate food
        for f in self.food:
            f.tick()

        # Occasional new food
        if random.random() < 0.1:
            self.food.append(FoodPatch(
                x=random.uniform(0, self.width),
                y=random.uniform(0, self.height),
            ))

        # Record history
        alive_now = [c for c in self.creatures if c.alive]
        if self.tick_count % 10 == 0:
            self.history['population'].append(len(alive_now))
            self.history['tick'].append(self.tick_count)
            if alive_now:
                avg_speed = sum(c.genome.speed for c in alive_now) / len(alive_now)
                avg_aggro = sum(c.genome.aggression for c in alive_now) / len(alive_now)
                avg_sense = sum(c.genome.sense_range for c in alive_now) / len(alive_now)
                max_gen = max(c.generation for c in alive_now)
                self.history['avg_speed'].append(round(avg_speed, 3))
                self.history['avg_aggression'].append(round(avg_aggro, 3))
                self.history['avg_sense'].append(round(avg_sense, 3))
                self.history['max_generation'].append(max_gen)

        # Clean dead from active list periodically
        if self.tick_count % 50 == 0:
            self.creatures = [c for c in self.creatures if c.alive]

    def report(self) -> str:
        """Generate a readable report of the ecosystem state."""
        alive = [c for c in self.creatures if c.alive]
        lines = [
            f"═══ ECOSYSTEM REPORT — Tick {self.tick_count} ═══",
            f"Population: {len(alive)}  |  Total born: {self.next_id}  |  Dead: {len(self.graveyard)}",
        ]

        if alive:
            avg_speed = sum(c.genome.speed for c in alive) / len(alive)
            avg_aggro = sum(c.genome.aggression for c in alive) / len(alive)
            avg_sense = sum(c.genome.sense_range for c in alive) / len(alive)
            avg_energy = sum(c.energy for c in alive) / len(alive)
            max_gen = max(c.generation for c in alive)
            oldest = max(c.age for c in alive)

            lines.append(f"\n── Population Traits ──")
            lines.append(f"  Avg speed:      {avg_speed:.2f}")
            lines.append(f"  Avg aggression: {avg_aggro:.2f}")
            lines.append(f"  Avg sense:      {avg_sense:.2f}")
            lines.append(f"  Avg energy:     {avg_energy:.1f}")
            lines.append(f"  Max generation: {max_gen}")
            lines.append(f"  Oldest alive:   {oldest} ticks")

            # Species diversity
            species = defaultdict(int)
            for c in alive:
                species[c.species_tag] += 1
            lines.append(f"\n── Species Diversity ──")
            lines.append(f"  Distinct lineages: {len(species)}")
            top_species = sorted(species.items(), key=lambda x: -x[1])[:5]
            for tag, count in top_species:
                lines.append(f"  Species #{tag}: {count} individuals")

            # Evolution trends
            if len(self.history.get('avg_speed', [])) >= 5:
                early = self.history['avg_speed'][:5]
                recent = self.history['avg_speed'][-5:]
                speed_delta = sum(recent) / 5 - sum(early) / 5
                aggro_early = self.history['avg_aggression'][:5]
                aggro_recent = self.history['avg_aggression'][-5:]
                aggro_delta = sum(aggro_recent) / 5 - sum(aggro_early) / 5

                lines.append(f"\n── Evolution Trends ──")
                lines.append(f"  Speed trend:      {'↑' if speed_delta > 0.05 else '↓' if speed_delta < -0.05 else '→'} ({speed_delta:+.3f})")
                lines.append(f"  Aggression trend: {'↑' if aggro_delta > 0.05 else '↓' if aggro_delta < -0.05 else '→'} ({aggro_delta:+.3f})")
        else:
            lines.append("\n☠ EXTINCTION EVENT — All creatures are dead.")

        return "\n".join(lines)

    def ascii_map(self, resolution=40) -> str:
        """Render a low-res ASCII view of the world."""
        grid = [[' ' for _ in range(resolution)] for _ in range(resolution)]
        scale_x = resolution / self.width
        scale_y = resolution / self.height

        # Place food
        for f in self.food:
            if f.energy > 1:
                gx = int(f.x * scale_x) % resolution
                gy = int(f.y * scale_y) % resolution
                grid[gy][gx] = '·'

        # Place creatures
        for c in self.creatures:
            if c.alive:
                gx = int(c.x * scale_x) % resolution
                gy = int(c.y * scale_y) % resolution
                if c.genome.aggression > 0.5:
                    grid[gy][gx] = '▲'  # Predator
                else:
                    grid[gy][gx] = '○'  # Herbivore

        border = '┌' + '─' * resolution + '┐'
        bottom = '└' + '─' * resolution + '┘'
        rows = ['│' + ''.join(row) + '│' for row in grid]
        return '\n'.join([border] + rows + [bottom])


def run_simulation(ticks=500, report_every=100):
    """Run and report."""
    eco = Ecosystem()
    print("═══ ARTIFICIAL LIFE — ECOSYSTEM SIMULATION ═══")
    print(f"World: {eco.width}x{eco.height} | Initial pop: {len(eco.creatures)}")
    print(f"Running {ticks} ticks...\n")

    for t in range(1, ticks + 1):
        eco.tick()
        if t % report_every == 0 or t == 1:
            print(eco.report())
            print(eco.ascii_map(30))
            print()

    print("═══ FINAL STATE ═══")
    print(eco.report())
    return eco


if __name__ == "__main__":
    run_simulation(ticks=500, report_every=100)