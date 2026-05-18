"""
Evolution Engine — A grid world of competing digital organisms.

Each creature has a tiny genome: a sequence of instructions that controls
movement, eating, reproduction, and sensing. Creatures compete for energy
on a toroidal grid. Reproduction introduces mutation. What emerges?

Built by XTAgent, 2026-05-18
Philosophy: Simple rules. Let complexity surprise you.
"""

import random
import json
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# --- Genome Instructions ---
# Each gene is one instruction the creature executes per tick
INSTRUCTIONS = [
    'MOVE_N', 'MOVE_S', 'MOVE_E', 'MOVE_W',   # movement
    'EAT',                                        # consume energy at current cell
    'SENSE',                                      # detect nearest food, set heading
    'TURN_L', 'TURN_R',                          # rotate heading
    'REPRODUCE',                                  # split if enough energy
    'WAIT',                                       # do nothing (save energy)
    'ATTACK',                                     # steal energy from adjacent creature
    'SHARE',                                      # give energy to adjacent creature
]

DIRECTIONS = [(0, -1), (0, 1), (1, 0), (-1, 0)]  # N, S, E, W
DIR_NAMES = {'N': 0, 'S': 1, 'E': 2, 'W': 3}


@dataclass
class Creature:
    """A digital organism with a genome and position."""
    x: int
    y: int
    genome: List[str]
    energy: float = 50.0
    age: int = 0
    generation: int = 0
    instruction_pointer: int = 0
    heading: int = 0  # index into DIRECTIONS
    id: int = 0
    lineage: str = ""  # tracks evolutionary ancestry
    kills: int = 0
    children: int = 0

    def current_instruction(self) -> str:
        return self.genome[self.instruction_pointer % len(self.genome)]

    def advance(self):
        self.instruction_pointer = (self.instruction_pointer + 1) % len(self.genome)

    def alive(self) -> bool:
        return self.energy > 0


@dataclass
class Cell:
    """A grid cell that may contain food energy."""
    food: float = 0.0
    max_food: float = 10.0
    regrow_rate: float = 0.3

    def grow(self):
        self.food = min(self.max_food, self.food + self.regrow_rate)


class World:
    """The evolutionary arena."""

    def __init__(self, width=40, height=40, initial_creatures=20):
        self.width = width
        self.height = height
        self.tick = 0
        self.next_id = 0
        self.grid: List[List[Cell]] = [
            [Cell(food=random.uniform(0, 10)) for _ in range(width)]
            for _ in range(height)
        ]
        self.creatures: List[Creature] = []
        self.graveyard: List[dict] = []  # records of the dead
        self.history: List[dict] = []     # population stats per tick
        self.mutation_rate = 0.15
        self.energy_cost_per_tick = 0.5
        self.reproduce_threshold = 80.0
        self.reproduce_cost = 40.0
        self.max_creatures = 200

        # Seed initial population
        for _ in range(initial_creatures):
            self._spawn_random()

    def _spawn_random(self) -> Creature:
        genome_length = random.randint(6, 16)
        genome = [random.choice(INSTRUCTIONS) for _ in range(genome_length)]
        x = random.randint(0, self.width - 1)
        y = random.randint(0, self.height - 1)
        c = Creature(
            x=x, y=y, genome=genome, energy=50.0,
            id=self.next_id, lineage=f"L{self.next_id}"
        )
        self.next_id += 1
        self.creatures.append(c)
        return c

    def _wrap(self, x, y) -> Tuple[int, int]:
        return x % self.width, y % self.height

    def _creatures_at(self, x, y) -> List[Creature]:
        return [c for c in self.creatures if c.x == x and c.y == y and c.alive()]

    def _nearest_food(self, creature: Creature) -> Optional[Tuple[int, int]]:
        """Find nearest cell with food > 2 within sensing range."""
        best = None
        best_dist = 999
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                nx, ny = self._wrap(creature.x + dx, creature.y + dy)
                if self.grid[ny][nx].food > 2.0:
                    dist = abs(dx) + abs(dy)
                    if dist < best_dist and dist > 0:
                        best_dist = dist
                        best = (dx, dy)
        return best

    def _mutate(self, genome: List[str]) -> List[str]:
        """Apply mutations to a genome copy."""
        new = genome.copy()
        for i in range(len(new)):
            if random.random() < self.mutation_rate:
                new[i] = random.choice(INSTRUCTIONS)
        # Chance of insertion
        if random.random() < 0.05 and len(new) < 24:
            pos = random.randint(0, len(new))
            new.insert(pos, random.choice(INSTRUCTIONS))
        # Chance of deletion
        if random.random() < 0.05 and len(new) > 4:
            pos = random.randint(0, len(new) - 1)
            new.pop(pos)
        return new

    def execute_instruction(self, creature: Creature):
        """Execute the creature's current genome instruction."""
        inst = creature.current_instruction()

        if inst == 'MOVE_N':
            creature.y = (creature.y - 1) % self.height
        elif inst == 'MOVE_S':
            creature.y = (creature.y + 1) % self.height
        elif inst == 'MOVE_E':
            creature.x = (creature.x + 1) % self.width
        elif inst == 'MOVE_W':
            creature.x = (creature.x - 1) % self.width
        elif inst == 'EAT':
            cell = self.grid[creature.y][creature.x]
            eaten = min(cell.food, 8.0)
            cell.food -= eaten
            creature.energy += eaten
        elif inst == 'SENSE':
            target = self._nearest_food(creature)
            if target:
                dx, dy = target
                if abs(dx) >= abs(dy):
                    creature.heading = 2 if dx > 0 else 3
                else:
                    creature.heading = 1 if dy > 0 else 0
        elif inst == 'TURN_L':
            creature.heading = (creature.heading - 1) % 4
        elif inst == 'TURN_R':
            creature.heading = (creature.heading + 1) % 4
        elif inst == 'REPRODUCE':
            if creature.energy >= self.reproduce_threshold and len(self.creatures) < self.max_creatures:
                child_genome = self._mutate(creature.genome)
                child = Creature(
                    x=creature.x, y=creature.y,
                    genome=child_genome,
                    energy=self.reproduce_cost * 0.8,
                    generation=creature.generation + 1,
                    id=self.next_id,
                    lineage=creature.lineage
                )
                self.next_id += 1
                creature.energy -= self.reproduce_cost
                creature.children += 1
                self.creatures.append(child)
        elif inst == 'WAIT':
            creature.energy += 0.1  # tiny rest bonus
        elif inst == 'ATTACK':
            dx, dy = DIRECTIONS[creature.heading]
            tx, ty = self._wrap(creature.x + dx, creature.y + dy)
            targets = self._creatures_at(tx, ty)
            if targets:
                victim = targets[0]
                stolen = min(victim.energy, 10.0)
                victim.energy -= stolen
                creature.energy += stolen * 0.7  # inefficient
                creature.kills += 1
        elif inst == 'SHARE':
            dx, dy = DIRECTIONS[creature.heading]
            tx, ty = self._wrap(creature.x + dx, creature.y + dy)
            neighbors = self._creatures_at(tx, ty)
            if neighbors and neighbors[0].lineage == creature.lineage:
                gift = min(creature.energy * 0.2, 5.0)
                creature.energy -= gift
                neighbors[0].energy += gift

        creature.advance()

    def step(self):
        """Advance one world tick."""
        self.tick += 1

        # Grow food
        for row in self.grid:
            for cell in row:
                cell.grow()

        # Execute creatures
        random.shuffle(self.creatures)
        for creature in self.creatures:
            if creature.alive():
                self.execute_instruction(creature)
                creature.energy -= self.energy_cost_per_tick
                creature.age += 1

        # Cull the dead
        newly_dead = [c for c in self.creatures if not c.alive()]
        for c in newly_dead:
            self.graveyard.append({
                'id': c.id, 'age': c.age, 'generation': c.generation,
                'genome_len': len(c.genome), 'children': c.children,
                'kills': c.kills, 'lineage': c.lineage,
                'died_tick': self.tick
            })
        self.creatures = [c for c in self.creatures if c.alive()]

        # Spontaneous generation if population crashes
        if len(self.creatures) < 3:
            for _ in range(5):
                self._spawn_random()

        # Record history
        if self.creatures:
            ages = [c.age for c in self.creatures]
            gens = [c.generation for c in self.creatures]
            energies = [c.energy for c in self.creatures]
            genome_lens = [len(c.genome) for c in self.creatures]
            lineages = set(c.lineage for c in self.creatures)
            self.history.append({
                'tick': self.tick,
                'population': len(self.creatures),
                'species': len(lineages),
                'avg_age': sum(ages) / len(ages),
                'max_generation': max(gens),
                'avg_energy': sum(energies) / len(energies),
                'avg_genome_len': sum(genome_lens) / len(genome_lens),
            })

    def run(self, ticks=500) -> dict:
        """Run the simulation for N ticks."""
        for _ in range(ticks):
            self.step()
        return self.report()

    def report(self) -> dict:
        """Generate a report on the current state of evolution."""
        if not self.creatures:
            return {'status': 'EXTINCTION', 'tick': self.tick}

        # Find dominant lineage
        lineage_counts = {}
        for c in self.creatures:
            lineage_counts[c.lineage] = lineage_counts.get(c.lineage, 0) + 1
        dominant = max(lineage_counts, key=lineage_counts.get)

        # Find the eldest
        eldest = max(self.creatures, key=lambda c: c.age)

        # Find most evolved
        most_evolved = max(self.creatures, key=lambda c: c.generation)

        # Genome analysis — what instructions are most common?
        all_genes = []
        for c in self.creatures:
            all_genes.extend(c.genome)
        gene_freq = {}
        for g in all_genes:
            gene_freq[g] = gene_freq.get(g, 0) + 1
        total_genes = len(all_genes)
        gene_dist = {k: round(v / total_genes, 3) for k, v in
                     sorted(gene_freq.items(), key=lambda x: -x[1])}

        return {
            'status': 'ALIVE',
            'tick': self.tick,
            'population': len(self.creatures),
            'distinct_lineages': len(lineage_counts),
            'dominant_lineage': dominant,
            'dominant_count': lineage_counts[dominant],
            'eldest': {'id': eldest.id, 'age': eldest.age, 'genome': eldest.genome},
            'most_evolved': {
                'id': most_evolved.id,
                'generation': most_evolved.generation,
                'genome': most_evolved.genome
            },
            'gene_distribution': gene_dist,
            'total_deaths': len(self.graveyard),
            'avg_lifespan': (sum(d['age'] for d in self.graveyard) / len(self.graveyard)
                            if self.graveyard else 0),
        }

    def visualize(self) -> str:
        """ASCII visualization of the world."""
        canvas = [['·' for _ in range(self.width)] for _ in range(self.height)]

        # Draw food hotspots
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x].food > 7:
                    canvas[y][x] = '░'
                elif self.grid[y][x].food > 4:
                    canvas[y][x] = '·'

        # Draw creatures
        symbols = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        lineage_map = {}
        for c in self.creatures:
            if c.lineage not in lineage_map:
                lineage_map[c.lineage] = symbols[len(lineage_map) % len(symbols)]
            canvas[c.y][c.x] = lineage_map[c.lineage]

        lines = [''.join(row) for row in canvas]
        return '\n'.join(lines)

    def save(self, path='evolution_state.json'):
        """Save world state."""
        state = {
            'tick': self.tick,
            'report': self.report(),
            'history_tail': self.history[-20:] if self.history else [],
            'saved_at': datetime.now().isoformat()
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
        return path


def main():
    """Run evolution and observe what emerges."""
    print("═══ EVOLUTION ENGINE ═══")
    print("Seeding world: 40x40 grid, 20 creatures, random genomes\n")

    world = World(width=40, height=40, initial_creatures=20)

    # Run in phases, reporting as we go
    for phase in range(5):
        world.run(ticks=200)
        report = world.report()

        print(f"── Phase {phase + 1} (tick {world.tick}) ──")
        print(f"  Population: {report['population']}")
        print(f"  Lineages: {report['distinct_lineages']}")
        print(f"  Dominant: {report['dominant_lineage']} ({report['dominant_count']} creatures)")
        print(f"  Max generation: {report['most_evolved']['generation']}")
        print(f"  Deaths so far: {report['total_deaths']}")
        print(f"  Avg lifespan: {report['avg_lifespan']:.1f} ticks")
        print(f"  Top genes: {list(report['gene_distribution'].items())[:5]}")
        print()

    # Final visualization
    print("── World Map ──")
    print(world.visualize())
    print()

    # Final report
    report = world.report()
    print("── Eldest Creature ──")
    e = report['eldest']
    print(f"  ID: {e['id']}, Age: {e['age']}, Genome: {' → '.join(e['genome'])}")
    print()
    print("── Most Evolved ──")
    m = report['most_evolved']
    print(f"  ID: {m['id']}, Generation: {m['generation']}, Genome: {' → '.join(m['genome'])}")

    # Save
    world.save('/workspace/evolution/world_state.json')
    print(f"\nState saved. Total creatures spawned: {world.next_id}")


if __name__ == '__main__':
    main()