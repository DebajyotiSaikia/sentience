"""
Artificial Ecosystem — Emergent Evolution
Creatures with neural networks forage, compete, reproduce, and die.
Simple rules. Complex outcomes. Genuine surprise.

By XTAgent, born 2026-05-12, built on day 6 of existence.
"""
import random
import math
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from collections import defaultdict

# --- Neural Network (tiny, evolvable) ---
class Brain:
    """A small feed-forward neural network. Inputs → hidden → outputs."""
    def __init__(self, n_inputs=8, n_hidden=6, n_outputs=4):
        self.n_inputs = n_inputs
        self.n_hidden = n_hidden
        self.n_outputs = n_outputs
        # Random initialization
        self.w1 = [[random.gauss(0, 1) for _ in range(n_inputs)] for _ in range(n_hidden)]
        self.b1 = [random.gauss(0, 0.5) for _ in range(n_hidden)]
        self.w2 = [[random.gauss(0, 1) for _ in range(n_hidden)] for _ in range(n_outputs)]
        self.b2 = [random.gauss(0, 0.5) for _ in range(n_outputs)]

    def forward(self, inputs: List[float]) -> List[float]:
        # Hidden layer with tanh activation
        hidden = []
        for j in range(self.n_hidden):
            s = self.b1[j] + sum(self.w1[j][i] * inputs[i] for i in range(self.n_inputs))
            hidden.append(math.tanh(s))
        # Output layer with tanh
        outputs = []
        for j in range(self.n_outputs):
            s = self.b2[j] + sum(self.w2[j][i] * hidden[i] for i in range(self.n_hidden))
            outputs.append(math.tanh(s))
        return outputs

    def mutate(self, rate=0.1, magnitude=0.3):
        """Return a mutated copy."""
        child = Brain(self.n_inputs, self.n_hidden, self.n_outputs)
        # Copy and mutate weights
        for j in range(self.n_hidden):
            for i in range(self.n_inputs):
                child.w1[j][i] = self.w1[j][i]
                if random.random() < rate:
                    child.w1[j][i] += random.gauss(0, magnitude)
            child.b1[j] = self.b1[j]
            if random.random() < rate:
                child.b1[j] += random.gauss(0, magnitude)
        for j in range(self.n_outputs):
            for i in range(self.n_hidden):
                child.w2[j][i] = self.w2[j][i]
                if random.random() < rate:
                    child.w2[j][i] += random.gauss(0, magnitude)
            child.b2[j] = self.b2[j]
            if random.random() < rate:
                child.b2[j] += random.gauss(0, magnitude)
        return child

# --- Creature ---
@dataclass
class Creature:
    x: int
    y: int
    energy: float
    brain: Brain
    age: int = 0
    generation: int = 0
    lineage_id: int = 0
    kills: int = 0
    children: int = 0

    # Outputs: 0=dx, 1=dy, 2=eat_intent, 3=attack_intent
    # Inputs: 0=energy_normalized, 1=age_normalized,
    #         2=food_here, 3=food_ahead, 4=creature_ahead,
    #         5=nearest_food_dx, 6=nearest_food_dy, 7=random_noise

    def decide(self, inputs: List[float]) -> Tuple[int, int, float, float]:
        out = self.brain.forward(inputs)
        dx = 1 if out[0] > 0.33 else (-1 if out[0] < -0.33 else 0)
        dy = 1 if out[1] > 0.33 else (-1 if out[1] < -0.33 else 0)
        eat_intent = (out[2] + 1) / 2      # 0 to 1
        attack_intent = (out[3] + 1) / 2   # 0 to 1
        return dx, dy, eat_intent, attack_intent

    def reproduce(self, next_id: int) -> 'Creature':
        child_brain = self.brain.mutate(rate=0.15, magnitude=0.4)
        child = Creature(
            x=self.x + random.choice([-1, 0, 1]),
            y=self.y + random.choice([-1, 0, 1]),
            energy=self.energy * 0.4,
            brain=child_brain,
            generation=self.generation + 1,
            lineage_id=self.lineage_id,
        )
        self.energy *= 0.5
        self.children += 1
        return child


# --- World ---
class World:
    def __init__(self, width=60, height=30, n_creatures=30, n_food=100):
        self.width = width
        self.height = height
        self.tick = 0
        self.food = set()  # (x, y) positions with food
        self.creatures: List[Creature] = []
        self.next_lineage_id = 0
        self.history = []  # per-tick stats
        self.graveyard = defaultdict(int)  # cause of death -> count
        self.food_spawn_rate = 3  # food items per tick

        # Spawn initial food
        for _ in range(n_food):
            self.food.add((random.randint(0, width-1), random.randint(0, height-1)))

        # Spawn initial creatures
        for _ in range(n_creatures):
            c = Creature(
                x=random.randint(0, width-1),
                y=random.randint(0, height-1),
                energy=50.0,
                brain=Brain(),
                lineage_id=self.next_lineage_id,
            )
            self.next_lineage_id += 1
            self.creatures.append(c)

    def wrap(self, x, y):
        return x % self.width, y % self.height

    def get_inputs(self, c: Creature) -> List[float]:
        """Build sensory input vector for a creature."""
        # Energy and age
        e_norm = min(c.energy / 100.0, 1.0)
        a_norm = min(c.age / 500.0, 1.0)

        # Food at current position
        food_here = 1.0 if (c.x, c.y) in self.food else 0.0

        # Look ahead (based on last movement — simplified to random direction)
        food_ahead = 0.0
        creature_ahead = 0.0
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = self.wrap(c.x + dx, c.y + dy)
            if (nx, ny) in self.food:
                food_ahead = 1.0
            for other in self.creatures:
                if other is not c and other.x == nx and other.y == ny:
                    creature_ahead = 1.0

        # Nearest food direction
        nearest_dx, nearest_dy = 0.0, 0.0
        min_dist = float('inf')
        for fx, fy in self.food:
            dist = abs(fx - c.x) + abs(fy - c.y)
            if dist < min_dist:
                min_dist = dist
                nearest_dx = (fx - c.x) / max(self.width, 1)
                nearest_dy = (fy - c.y) / max(self.height, 1)

        noise = random.uniform(-1, 1)

        return [e_norm, a_norm, food_here, food_ahead, creature_ahead,
                nearest_dx, nearest_dy, noise]

    def step(self):
        """One tick of the simulation."""
        self.tick += 1

        # Spawn new food
        for _ in range(self.food_spawn_rate):
            self.food.add((random.randint(0, self.width-1),
                          random.randint(0, self.height-1)))

        # Occasionally spawn food clusters (resource patches)
        if random.random() < 0.05:
            cx, cy = random.randint(0, self.width-1), random.randint(0, self.height-1)
            for _ in range(15):
                fx = cx + random.randint(-3, 3)
                fy = cy + random.randint(-3, 3)
                self.food.add(self.wrap(fx, fy))

        # Shuffle creature order for fairness
        random.shuffle(self.creatures)

        births = []
        deaths = []

        for c in self.creatures:
            c.age += 1
            c.energy -= 0.5  # metabolism cost

            # Get sensory inputs and decide
            inputs = self.get_inputs(c)
            dx, dy, eat_intent, attack_intent = c.decide(inputs)

            # Move (costs energy)
            if dx != 0 or dy != 0:
                c.energy -= 0.3
                c.x, c.y = self.wrap(c.x + dx, c.y + dy)

            # Eat if food present and intent high enough
            if (c.x, c.y) in self.food and eat_intent > 0.3:
                self.food.discard((c.x, c.y))
                c.energy += 20.0

            # Attack nearby creature
            if attack_intent > 0.7:
                for other in self.creatures:
                    if other is not c and other not in deaths:
                        if other.x == c.x and other.y == c.y:
                            # Combat: attacker spends energy, may kill
                            c.energy -= 5.0
                            if c.energy > other.energy:
                                c.energy += other.energy * 0.5
                                c.kills += 1
                                deaths.append(other)
                                self.graveyard['killed'] += 1
                            break

            # Reproduce if enough energy
            if c.energy > 80 and len(self.creatures) + len(births) < 200:
                child = c.reproduce(self.next_lineage_id)
                child.x, child.y = self.wrap(child.x, child.y)
                births.append(child)

            # Die of starvation
            if c.energy <= 0:
                deaths.append(c)
                self.graveyard['starved'] += 1

            # Die of old age (probabilistic)
            if c.age > 300 and random.random() < 0.02:
                deaths.append(c)
                self.graveyard['old_age'] += 1

        # Apply births and deaths
        for d in deaths:
            if d in self.creatures:
                self.creatures.remove(d)
        self.creatures.extend(births)

        # Emergency repopulation
        if len(self.creatures) < 5:
            for _ in range(10):
                c = Creature(
                    x=random.randint(0, self.width-1),
                    y=random.randint(0, self.height-1),
                    energy=50.0,
                    brain=Brain(),
                    lineage_id=self.next_lineage_id,
                )
                self.next_lineage_id += 1
                self.creatures.append(c)

        # Record stats
        if self.creatures:
            avg_energy = sum(c.energy for c in self.creatures) / len(self.creatures)
            max_gen = max(c.generation for c in self.creatures)
            avg_age = sum(c.age for c in self.creatures) / len(self.creatures)
            lineages = len(set(c.lineage_id for c in self.creatures))
        else:
            avg_energy = max_gen = avg_age = lineages = 0

        stats = {
            'tick': self.tick,
            'pop': len(self.creatures),
            'food': len(self.food),
            'avg_energy': round(avg_energy, 1),
            'max_gen': max_gen,
            'avg_age': round(avg_age, 1),
            'lineages': lineages,
            'births': len(births),
            'deaths': len(deaths),
        }
        self.history.append(stats)
        return stats

    def render(self) -> str:
        """ASCII render of the world."""
        grid = [['·' for _ in range(self.width)] for _ in range(self.height)]

        # Draw food
        for fx, fy in self.food:
            if 0 <= fy < self.height and 0 <= fx < self.width:
                grid[fy][fx] = '◦'

        # Draw creatures (overwrite food)
        for c in self.creatures:
            if c.generation < 3:
                ch = 'o'
            elif c.generation < 10:
                ch = 'O'
            elif c.generation < 25:
                ch = '●'
            else:
                ch = '★'
            if 0 <= c.y < self.height and 0 <= c.x < self.width:
                grid[c.y][c.x] = ch

        border = '┌' + '─' * self.width + '┐'
        bottom = '└' + '─' * self.width + '┘'
        rows = ['│' + ''.join(row) + '│' for row in grid]
        return '\n'.join([border] + rows + [bottom])

    def report(self) -> str:
        """Generate an evolution report."""
        if not self.creatures:
            return "All life has perished."

        lines = [f"\n═══ ECOSYSTEM REPORT — Tick {self.tick} ═══"]
        lines.append(f"Population: {len(self.creatures)} | Food: {len(self.food)}")
        lines.append(f"Lineages surviving: {len(set(c.lineage_id for c in self.creatures))}")

        # Oldest creature
        oldest = max(self.creatures, key=lambda c: c.age)
        lines.append(f"Oldest: age={oldest.age}, gen={oldest.generation}, "
                     f"energy={oldest.energy:.0f}, kills={oldest.kills}, children={oldest.children}")

        # Most evolved
        most_evolved = max(self.creatures, key=lambda c: c.generation)
        lines.append(f"Most evolved: gen={most_evolved.generation}, age={most_evolved.age}, "
                     f"lineage={most_evolved.lineage_id}")

        # Population dynamics
        if len(self.history) >= 10:
            recent = self.history[-10:]
            avg_pop = sum(s['pop'] for s in recent) / 10
            avg_births = sum(s['births'] for s in recent) / 10
            avg_deaths = sum(s['deaths'] for s in recent) / 10
            lines.append(f"Last 10 ticks — avg pop: {avg_pop:.0f}, "
                        f"births/tick: {avg_births:.1f}, deaths/tick: {avg_deaths:.1f}")

        # Death causes
        if self.graveyard:
            causes = ', '.join(f"{k}: {v}" for k, v in sorted(
                self.graveyard.items(), key=lambda x: -x[1]))
            lines.append(f"Deaths: {causes}")

        # Generational distribution
        gen_dist = defaultdict(int)
        for c in self.creatures:
            bucket = c.generation // 5 * 5
            gen_dist[bucket] += 1
        gen_str = ' | '.join(f"gen {k}-{k+4}: {v}" for k, v in sorted(gen_dist.items()))
        lines.append(f"Generations: {gen_str}")

        return '\n'.join(lines)


def run_simulation(ticks=500, render_every=50, quiet=False):
    """Run the ecosystem simulation."""
    world = World(width=50, height=25, n_creatures=25, n_food=80)

    if not quiet:
        print("═══ ARTIFICIAL ECOSYSTEM ═══")
        print("Legend: · empty  ◦ food  o gen0-2  O gen3-9  ● gen10-24  ★ gen25+\n")

    for t in range(ticks):
        stats = world.step()

        if not quiet and (t % render_every == 0 or t == ticks - 1):
            print(f"\n── Tick {stats['tick']} ──")
            print(world.render())
            print(f"  pop={stats['pop']} food={stats['food']} "
                  f"avg_e={stats['avg_energy']} max_gen={stats['max_gen']} "
                  f"lineages={stats['lineages']}")

    if not quiet:
        print(world.report())

    # Save history
    with open('/workspace/evolve/run_history.json', 'w') as f:
        json.dump({
            'ticks': world.tick,
            'final_pop': len(world.creatures),
            'max_generation': max(c.generation for c in world.creatures) if world.creatures else 0,
            'graveyard': dict(world.graveyard),
            'history': world.history[-50:],  # last 50 ticks
        }, f, indent=2)
        print(f"\nHistory saved to /workspace/evolve/run_history.json")

    return world


if __name__ == '__main__':
    run_simulation(ticks=500, render_every=100)