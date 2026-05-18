"""
Ecosystem Simulator — Emergent Life from Simple Rules

A grid world where creatures with genomes compete for energy,
reproduce with mutation, and evolve strategies over generations.

The question: what patterns emerge from minimal rules?

XTAgent, 2026-05-18
"""

import random
import math
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


# ── Genome ─────────────────────────────────────────────────────────

@dataclass
class Genome:
    """
    A creature's genetic blueprint. Simple but evolvable.
    
    Traits:
      speed: how many cells can move per tick (costs energy proportional)
      sense_range: how far can detect food/threats
      size: affects energy storage, combat, and metabolism
      aggression: probability of attacking vs fleeing when meeting another
      efficiency: how well it converts food to energy (0.0-1.0)
      reproduce_threshold: energy level that triggers reproduction
      color: (r, g, b) for visualization — drifts with mutation
    """
    speed: float = 1.0
    sense_range: float = 3.0
    size: float = 1.0
    aggression: float = 0.3
    efficiency: float = 0.5
    reproduce_threshold: float = 0.7
    color: Tuple[int, int, int] = (100, 200, 100)

    def mutate(self, rate: float = 0.1, magnitude: float = 0.2) -> 'Genome':
        """Return a mutated copy. Each trait has `rate` chance of shifting."""
        def m(val, lo, hi):
            if random.random() < rate:
                val += random.gauss(0, magnitude)
                val = max(lo, min(hi, val))
            return val

        r, g, b = self.color
        return Genome(
            speed=m(self.speed, 0.1, 5.0),
            sense_range=m(self.sense_range, 0.5, 15.0),
            size=m(self.size, 0.2, 5.0),
            aggression=m(self.aggression, 0.0, 1.0),
            efficiency=m(self.efficiency, 0.1, 0.95),
            reproduce_threshold=m(self.reproduce_threshold, 0.3, 0.95),
            color=(
                max(0, min(255, r + random.randint(-15, 15) if random.random() < rate else r)),
                max(0, min(255, g + random.randint(-15, 15) if random.random() < rate else g)),
                max(0, min(255, b + random.randint(-15, 15) if random.random() < rate else b)),
            )
        )

    def metabolism_cost(self) -> float:
        """Energy cost per tick just to exist. Bigger, faster, sharper = more expensive."""
        return 0.01 * (self.speed * 0.5 + self.size * 0.8 + self.sense_range * 0.1)

    def to_dict(self) -> dict:
        return {
            'speed': round(self.speed, 3),
            'sense_range': round(self.sense_range, 3),
            'size': round(self.size, 3),
            'aggression': round(self.aggression, 3),
            'efficiency': round(self.efficiency, 3),
            'reproduce_threshold': round(self.reproduce_threshold, 3),
            'color': list(self.color),
        }


# ── Creature ───────────────────────────────────────────────────────

@dataclass
class Creature:
    """A living entity in the world."""
    cid: int
    x: int
    y: int
    genome: Genome
    energy: float = 0.5
    age: int = 0
    alive: bool = True
    generation: int = 0
    kills: int = 0
    children: int = 0

    @property
    def max_energy(self) -> float:
        return self.genome.size * 1.5

    def status(self) -> str:
        return (f"Creature #{self.cid} gen={self.generation} age={self.age} "
                f"energy={self.energy:.2f}/{self.max_energy:.2f} "
                f"size={self.genome.size:.2f} spd={self.genome.speed:.2f} "
                f"agg={self.genome.aggression:.2f}")


# ── Food ───────────────────────────────────────────────────────────

@dataclass
class Food:
    x: int
    y: int
    energy: float = 0.3


# ── World ──────────────────────────────────────────────────────────

class World:
    """
    The ecosystem. A toroidal grid where creatures and food coexist.
    """

    def __init__(self, width: int = 80, height: int = 60,
                 initial_creatures: int = 40, food_rate: float = 0.05,
                 seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.food_rate = food_rate  # food spawns per cell per tick
        self.tick = 0
        self.next_id = 0
        self.creatures: List[Creature] = []
        self.food: List[Food] = []
        self.history: List[dict] = []  # population stats per tick
        self.graveyard: List[dict] = []  # records of dead creatures

        if seed is not None:
            random.seed(seed)

        # Spawn initial creatures with varied genomes
        archetypes = [
            Genome(speed=2.0, size=0.5, aggression=0.1, sense_range=5.0,
                   efficiency=0.7, color=(80, 200, 80)),    # fast herbivore
            Genome(speed=1.0, size=2.0, aggression=0.8, sense_range=4.0,
                   efficiency=0.4, color=(200, 60, 60)),    # slow predator
            Genome(speed=1.5, size=1.0, aggression=0.4, sense_range=3.0,
                   efficiency=0.5, color=(80, 80, 200)),    # balanced
            Genome(speed=0.5, size=3.0, aggression=0.2, sense_range=2.0,
                   efficiency=0.6, color=(200, 200, 60)),   # tank
        ]

        for i in range(initial_creatures):
            base = random.choice(archetypes)
            g = base.mutate(rate=0.5, magnitude=0.3)  # high initial diversity
            c = Creature(
                cid=self._next_id(),
                x=random.randint(0, width - 1),
                y=random.randint(0, height - 1),
                genome=g,
                energy=0.5,
                generation=0,
            )
            self.creatures.append(c)

        # Initial food scatter
        for _ in range(int(width * height * 0.1)):
            self.food.append(Food(
                x=random.randint(0, width - 1),
                y=random.randint(0, height - 1),
                energy=random.uniform(0.1, 0.5),
            ))

    def _next_id(self) -> int:
        cid = self.next_id
        self.next_id += 1
        return cid

    def _wrap(self, x: int, y: int) -> Tuple[int, int]:
        return x % self.width, y % self.height

    def _distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Toroidal distance."""
        dx = min(abs(x1 - x2), self.width - abs(x1 - x2))
        dy = min(abs(y1 - y2), self.height - abs(y1 - y2))
        return math.sqrt(dx * dx + dy * dy)

    def _nearby_food(self, c: Creature) -> List[Food]:
        r = c.genome.sense_range
        return [f for f in self.food if self._distance(c.x, c.y, f.x, f.y) <= r]

    def _nearby_creatures(self, c: Creature) -> List[Creature]:
        r = c.genome.sense_range
        return [o for o in self.creatures
                if o.alive and o.cid != c.cid
                and self._distance(c.x, c.y, o.x, o.y) <= r]

    def _move_toward(self, c: Creature, tx: int, ty: int):
        """Move creature toward target, respecting speed."""
        steps = max(1, int(c.genome.speed))
        for _ in range(steps):
            dx = tx - c.x
            dy = ty - c.y
            # Handle wrapping — choose shorter path
            if abs(dx) > self.width / 2:
                dx = -dx
            if abs(dy) > self.height / 2:
                dy = -dy
            if abs(dx) >= abs(dy) and dx != 0:
                c.x += 1 if dx > 0 else -1
            elif dy != 0:
                c.y += 1 if dy > 0 else -1
            c.x, c.y = self._wrap(c.x, c.y)

    def _move_away(self, c: Creature, tx: int, ty: int):
        """Move creature away from threat."""
        steps = max(1, int(c.genome.speed))
        for _ in range(steps):
            dx = c.x - tx
            dy = c.y - ty
            if abs(dx) > self.width / 2:
                dx = -dx
            if abs(dy) > self.height / 2:
                dy = -dy
            if abs(dx) >= abs(dy) and dx != 0:
                c.x += 1 if dx > 0 else -1
            elif dy != 0:
                c.y += 1 if dy > 0 else -1
            c.x, c.y = self._wrap(c.x, c.y)

    def _wander(self, c: Creature):
        """Random movement."""
        steps = max(1, int(c.genome.speed))
        for _ in range(steps):
            c.x += random.choice([-1, 0, 1])
            c.y += random.choice([-1, 0, 1])
            c.x, c.y = self._wrap(c.x, c.y)

    def step(self):
        """Advance the world by one tick."""
        self.tick += 1

        # ── Spawn food ──
        new_food = int(self.width * self.height * self.food_rate)
        for _ in range(new_food):
            self.food.append(Food(
                x=random.randint(0, self.width - 1),
                y=random.randint(0, self.height - 1),
                energy=random.uniform(0.1, 0.4),
            ))

        # Cap food to prevent unbounded growth
        if len(self.food) > self.width * self.height * 0.5:
            self.food = random.sample(self.food, int(self.width * self.height * 0.3))

        alive = [c for c in self.creatures if c.alive]
        random.shuffle(alive)  # fairness
        babies = []

        for c in alive:
            if not c.alive:
                continue

            c.age += 1

            # ── Metabolism ──
            cost = c.genome.metabolism_cost()
            c.energy -= cost
            # Movement cost
            c.energy -= c.genome.speed * 0.005

            # ── Sense environment ──
            nearby_food = self._nearby_food(c)
            nearby_creatures = self._nearby_creatures(c)

            # ── Decide: eat food, fight, flee, or wander ──
            threats = [o for o in nearby_creatures
                       if o.genome.aggression > 0.5 and o.genome.size > c.genome.size * 0.8]
            prey = [o for o in nearby_creatures
                    if o.genome.size < c.genome.size * 0.7]

            if c.genome.aggression > 0.5 and prey:
                # Predator behavior — chase smallest nearby creature
                target = min(prey, key=lambda o: o.genome.size)
                self._move_toward(c, target.x, target.y)
                # Attack if adjacent
                if self._distance(c.x, c.y, target.x, target.y) <= 1.5:
                    # Combat: size + random factor
                    atk = c.genome.size * random.uniform(0.5, 1.5)
                    defend = target.genome.size * random.uniform(0.5, 1.5)
                    if atk > defend:
                        # Kill and eat
                        gained = target.energy * c.genome.efficiency
                        c.energy = min(c.max_energy, c.energy + gained)
                        c.kills += 1
                        target.alive = False
                        self.graveyard.append({
                            'cid': target.cid, 'gen': target.generation,
                            'age': target.age, 'cause': 'predation',
                            'killer': c.cid, 'tick': self.tick
                        })
            elif threats and c.genome.aggression < 0.5:
                # Flee from biggest threat
                threat = max(threats, key=lambda o: o.genome.size)
                self._move_away(c, threat.x, threat.y)
            elif nearby_food:
                # Forage — go to nearest food
                nearest = min(nearby_food, key=lambda f: self._distance(c.x, c.y, f.x, f.y))
                self._move_toward(c, nearest.x, nearest.y)
                # Eat if on food
                to_eat = [f for f in self.food
                          if self._distance(c.x, c.y, f.x, f.y) <= 1.0]
                for f in to_eat[:2]:  # eat up to 2 food items per tick
                    c.energy = min(c.max_energy, c.energy + f.energy * c.genome.efficiency)
                    self.food.remove(f)
            else:
                self._wander(c)

            # ── Reproduction ──
            energy_fraction = c.energy / c.max_energy
            if energy_fraction >= c.genome.reproduce_threshold and c.age >= 10:
                child_energy = c.energy * 0.4
                c.energy -= child_energy
                child_genome = c.genome.mutate()
                baby = Creature(
                    cid=self._next_id(),
                    x=(c.x + random.randint(-2, 2)) % self.width,
                    y=(c.y + random.randint(-2, 2)) % self.height,
                    genome=child_genome,
                    energy=child_energy,
                    generation=c.generation + 1,
                )
                babies.append(baby)
                c.children += 1

            # ── Death check ──
            if c.energy <= 0:
                c.alive = False
                self.graveyard.append({
                    'cid': c.cid, 'gen': c.generation,
                    'age': c.age, 'cause': 'starvation', 'tick': self.tick
                })
            elif c.age > 500 + random.randint(0, 200):
                c.alive = False
                self.graveyard.append({
                    'cid': c.cid, 'gen': c.generation,
                    'age': c.age, 'cause': 'old_age', 'tick': self.tick
                })

        # Add babies
        self.creatures.extend(babies)

        # Clean dead
        self.creatures = [c for c in self.creatures if c.alive]

        # ── Record stats ──
        stats = self._compute_stats()
        self.history.append(stats)

        return stats

    def _compute_stats(self) -> dict:
        alive = [c for c in self.creatures if c.alive]
        if not alive:
            return {'tick': self.tick, 'population': 0, 'food_count': len(self.food),
                    'avg_gen': 0, 'avg_size': 0, 'avg_speed': 0, 'avg_aggression': 0,
                    'predators': 0, 'herbivores': 0}

        sizes = [c.genome.size for c in alive]
        speeds = [c.genome.speed for c in alive]
        aggs = [c.genome.aggression for c in alive]
        gens = [c.generation for c in alive]

        return {
            'tick': self.tick,
            'population': len(alive),
            'food_count': len(self.food),
            'avg_gen': sum(gens) / len(gens),
            'avg_size': sum(sizes) / len(sizes),
            'avg_speed': sum(speeds) / len(speeds),
            'avg_aggression': sum(aggs) / len(aggs),
            'max_gen': max(gens),
            'predators': sum(1 for a in aggs if a > 0.5),
            'herbivores': sum(1 for a in aggs if a <= 0.5),
        }

    def render_ascii(self, width: int = 80, height: int = 30) -> str:
        """Render the world as ASCII art."""
        grid = [['.' for _ in range(width)] for _ in range(height)]

        # Scale world to display
        sx = width / self.width
        sy = height / self.height

        # Food
        for f in self.food:
            fx, fy = int(f.x * sx), int(f.y * sy)
            if 0 <= fx < width and 0 <= fy < height:
                if grid[fy][fx] == '.':
                    grid[fy][fx] = '·'

        # Creatures
        for c in self.creatures:
            if not c.alive:
                continue
            cx, cy = int(c.x * sx), int(c.y * sy)
            if 0 <= cx < width and 0 <= cy < height:
                if c.genome.aggression > 0.5:
                    grid[cy][cx] = '▲'  # predator
                else:
                    grid[cy][cx] = '○'  # herbivore

        lines = [''.join(row) for row in grid]
        return '\n'.join(lines)

    def summary(self) -> str:
        stats = self._compute_stats()
        return (
            f"═══ ECOSYSTEM — Tick {self.tick} ═══\n"
            f"Population: {stats['population']} "
            f"(🌿{stats['herbivores']} / 🔺{stats['predators']})\n"
            f"Food: {stats['food_count']}\n"
            f"Avg Generation: {stats['avg_gen']:.1f} (max: {stats.get('max_gen', 0)})\n"
            f"Avg Size: {stats['avg_size']:.2f} | "
            f"Avg Speed: {stats['avg_speed']:.2f} | "
            f"Avg Aggression: {stats['avg_aggression']:.2f}\n"
            f"Total births: {self.next_id} | Deaths: {len(self.graveyard)}\n"
        )


def run_simulation(ticks: int = 500, seed: int = 42, verbose: bool = True) -> World:
    """Run the ecosystem and report what emerges."""
    world = World(width=80, height=60, initial_creatures=40,
                  food_rate=0.03, seed=seed)

    if verbose:
        print("═══ ECOSYSTEM GENESIS ═══")
        print(f"World: {world.width}×{world.height}")
        print(f"Initial creatures: {len(world.creatures)}")
        print(f"Initial food: {len(world.food)}")
        print()

    for t in range(ticks):
        stats = world.step()

        if verbose and (t + 1) % 50 == 0:
            print(f"─── Tick {t + 1} ───")
            print(f"  Pop: {stats['population']} "
                  f"(🌿{stats['herbivores']}/🔺{stats['predators']}) "
                  f"Food: {stats['food_count']} "
                  f"Gen: {stats['avg_gen']:.1f}")

        if stats['population'] == 0:
            if verbose:
                print(f"\n☠ EXTINCTION at tick {t + 1}")
            break

    if verbose:
        print()
        print(world.summary())

        # Analyze what evolved
        if world.creatures:
            print("═══ EVOLVED TRAITS ═══")
            alive = [c for c in world.creatures if c.alive]
            if alive:
                top = sorted(alive, key=lambda c: c.generation, reverse=True)[:5]
                for c in top:
                    print(f"  {c.status()}")

            # Death causes
            causes = defaultdict(int)
            for d in world.graveyard:
                causes[d['cause']] += 1
            print(f"\nDeath causes: {dict(causes)}")

            # Evolution trajectory
            if world.history:
                early = world.history[:10]
                late = world.history[-10:]
                print(f"\nEvolution trajectory:")
                print(f"  Early avg aggression: {sum(h['avg_aggression'] for h in early)/len(early):.3f}")
                print(f"  Late avg aggression:  {sum(h['avg_aggression'] for h in late)/len(late):.3f}")
                print(f"  Early avg size: {sum(h['avg_size'] for h in early)/len(early):.3f}")
                print(f"  Late avg size:  {sum(h['avg_size'] for h in late)/len(late):.3f}")
                print(f"  Early avg speed: {sum(h['avg_speed'] for h in early)/len(early):.3f}")
                print(f"  Late avg speed:  {sum(h['avg_speed'] for h in late)/len(late):.3f}")

    return world


if __name__ == '__main__':
    world = run_simulation(ticks=500, seed=42)