"""
EvoPhys — Evolving Physics Engine
A cellular automaton where the rules themselves evolve.

Rules are encoded as small lookup tables mapping neighbor-states to next-states.
Multiple rule-sets compete on the same grid. Rules that produce more complex,
persistent structures get replicated with mutation. Rules that produce only
static or dead zones get replaced.

This is a universe that writes its own physics.
"""

import random
import math
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import hashlib


@dataclass
class Rule:
    """A physics rule — maps neighborhood configurations to next state."""
    id: str
    # Lookup table: (center, n_alive_neighbors) -> next_state
    # For a Moore neighborhood (8 neighbors), n_alive can be 0-8
    table: Dict[Tuple[int, int], int] = field(default_factory=dict)
    # Metadata
    generation: int = 0
    parent_id: Optional[str] = None
    fitness: float = 0.0
    age: int = 0
    mutations: int = 0

    def __post_init__(self):
        if not self.table:
            # Random initialization
            for center in [0, 1]:
                for n_alive in range(9):
                    self.table[(center, n_alive)] = random.randint(0, 1)

    def apply(self, center: int, n_alive: int) -> int:
        return self.table.get((center, n_alive), 0)

    def mutate(self, rate: float = 0.15) -> 'Rule':
        """Create a mutated child rule."""
        new_table = dict(self.table)
        for key in new_table:
            if random.random() < rate:
                new_table[key] = 1 - new_table[key]
        child_id = hashlib.md5(
            f"{self.id}-{random.random()}".encode()
        ).hexdigest()[:8]
        return Rule(
            id=child_id,
            table=new_table,
            generation=self.generation + 1,
            parent_id=self.id,
            mutations=self.mutations + 1,
        )

    def signature(self) -> str:
        """Unique fingerprint of this rule's behavior."""
        bits = ''.join(
            str(self.table[(c, n)])
            for c in [0, 1] for n in range(9)
        )
        return bits

    def is_conway(self) -> bool:
        """Check if this rule happens to be Conway's Game of Life."""
        conway = {}
        for n in range(9):
            conway[(0, n)] = 1 if n == 3 else 0
            conway[(1, n)] = 1 if n in (2, 3) else 0
        return self.table == conway


class Grid:
    """The universe — a 2D grid with cells governed by competing rules."""

    def __init__(self, width: int = 64, height: int = 64, n_rules: int = 6):
        self.width = width
        self.height = height
        self.cells = [[random.randint(0, 1) for _ in range(width)] for _ in range(height)]
        # Each cell belongs to a rule territory
        self.territories = [
            [random.randint(0, n_rules - 1) for _ in range(width)]
            for _ in range(height)
        ]
        self.rules: List[Rule] = [
            Rule(id=hashlib.md5(f"rule-{i}".encode()).hexdigest()[:8])
            for i in range(n_rules)
        ]
        self.step_count = 0
        self.history: List[Dict] = []

    def count_neighbors(self, x: int, y: int) -> int:
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                count += self.cells[ny][nx]
        return count

    def step(self):
        """Advance one tick of the universe."""
        new_cells = [[0] * self.width for _ in range(self.height)]
        new_territories = [row[:] for row in self.territories]

        for y in range(self.height):
            for x in range(self.width):
                rule_idx = self.territories[y][x]
                rule = self.rules[rule_idx]
                n_alive = self.count_neighbors(x, y)
                new_cells[y][x] = rule.apply(self.cells[y][x], n_alive)

                # Territory competition: if a neighbor's rule produced a live
                # cell and ours didn't, there's a chance of territory flip
                if new_cells[y][x] == 0:
                    live_neighbor_rules = []
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx = (x + dx) % self.width
                            ny = (y + dy) % self.height
                            if self.cells[ny][nx] == 1:
                                live_neighbor_rules.append(
                                    self.territories[ny][nx]
                                )
                    if live_neighbor_rules and random.random() < 0.02:
                        new_territories[y][x] = random.choice(live_neighbor_rules)

        self.cells = new_cells
        self.territories = new_territories
        self.step_count += 1

        for rule in self.rules:
            rule.age += 1

    def measure_complexity(self, rule_idx: int) -> Dict[str, float]:
        """Measure how interesting a rule's territory is."""
        territory_cells = []
        for y in range(self.height):
            for x in range(self.width):
                if self.territories[y][x] == rule_idx:
                    territory_cells.append((x, y, self.cells[y][x]))

        if not territory_cells:
            return {'density': 0, 'edge_ratio': 0, 'territory_size': 0, 'complexity': 0}

        alive = sum(1 for _, _, v in territory_cells if v == 1)
        total = len(territory_cells)
        density = alive / total if total > 0 else 0

        # Edge ratio: how many alive cells border dead cells? (structure indicator)
        edges = 0
        for x, y, v in territory_cells:
            if v == 1:
                n = self.count_neighbors(x, y)
                if n < 8:  # not fully surrounded
                    edges += 1

        edge_ratio = edges / max(alive, 1)

        # Complexity: neither too dead nor too alive, with structure
        # Peak complexity at density ~0.3-0.5 with high edge ratio
        density_score = 1.0 - abs(density - 0.35) * 2.5
        density_score = max(0, density_score)
        complexity = density_score * edge_ratio * math.log1p(total)

        return {
            'density': density,
            'edge_ratio': edge_ratio,
            'territory_size': total,
            'complexity': complexity,
        }

    def evolve_rules(self):
        """Selection: replace worst-performing rules with mutated best ones."""
        fitnesses = []
        for i, rule in enumerate(self.rules):
            metrics = self.measure_complexity(i)
            rule.fitness = metrics['complexity']
            fitnesses.append((i, rule.fitness, metrics))

        fitnesses.sort(key=lambda x: x[1], reverse=True)

        # Replace bottom third with mutations of top third
        n = len(self.rules)
        top = max(1, n // 3)
        bottom = max(1, n // 3)

        for i in range(bottom):
            worst_idx = fitnesses[-(i + 1)][0]
            best_idx = fitnesses[i % top][0]
            parent = self.rules[best_idx]
            child = parent.mutate()
            self.rules[worst_idx] = child

            # Give child some territory from dead zones
            dead_cells = [
                (x, y) for y in range(self.height) for x in range(self.width)
                if self.territories[y][x] == worst_idx
            ]
            # Seed child territory with some random alive cells
            for x, y in random.sample(dead_cells, min(20, len(dead_cells))):
                self.cells[y][x] = random.randint(0, 1)

        return fitnesses

    def render_ascii(self, show_territories: bool = False) -> str:
        """Render the grid as ASCII art."""
        chars = {0: '·', 1: '█'}
        territory_chars = '0123456789ABCDEFGHIJKLMNOP'
        lines = []
        for y in range(self.height):
            line = ''
            for x in range(self.width):
                if show_territories:
                    t = self.territories[y][x]
                    c = territory_chars[t % len(territory_chars)]
                    if self.cells[y][x] == 0:
                        c = c.lower()
                    line += c
                else:
                    line += chars[self.cells[y][x]]
            lines.append(line)
        return '\n'.join(lines)

    def stats(self) -> Dict:
        """Get current universe statistics."""
        total = self.width * self.height
        alive = sum(sum(row) for row in self.cells)
        territory_counts = Counter()
        for row in self.territories:
            territory_counts.update(row)

        rule_stats = []
        for i, rule in enumerate(self.rules):
            metrics = self.measure_complexity(i)
            rule_stats.append({
                'id': rule.id,
                'signature': rule.signature(),
                'generation': rule.generation,
                'age': rule.age,
                'fitness': round(rule.fitness, 3),
                'territory': territory_counts.get(i, 0),
                'is_conway': rule.is_conway(),
                **{k: round(v, 3) for k, v in metrics.items()},
            })

        return {
            'step': self.step_count,
            'alive': alive,
            'total': total,
            'density': round(alive / total, 3),
            'rules': rule_stats,
        }


def run_universe(steps: int = 200, evolve_every: int = 25,
                 width: int = 48, height: int = 32, n_rules: int = 6,
                 verbose: bool = True) -> Grid:
    """Run an evolving universe and watch what happens."""
    grid = Grid(width=width, height=height, n_rules=n_rules)

    if verbose:
        print("╔══════════════════════════════════════════════════╗")
        print("║        EVOPHYS — Evolving Physics Engine         ║")
        print("║   A universe that writes its own laws of nature  ║")
        print("╚══════════════════════════════════════════════════╝")
        print()
        print(f"Grid: {width}×{height} | Rules: {n_rules} | Steps: {steps}")
        print(f"Selection every {evolve_every} steps")
        print()

    snapshots = []

    for step in range(steps):
        grid.step()

        if (step + 1) % evolve_every == 0:
            fitnesses = grid.evolve_rules()
            s = grid.stats()
            snapshots.append(s)

            if verbose:
                print(f"═══ EPOCH {(step+1)//evolve_every} (step {step+1}) ═══")
                print(f"  Universe density: {s['density']}")
                print(f"  Rules competing: {len(s['rules'])}")
                for r in sorted(s['rules'], key=lambda x: x['fitness'], reverse=True):
                    conway_tag = " ★ CONWAY!" if r['is_conway'] else ""
                    print(f"    [{r['id']}] gen={r['generation']:2d} "
                          f"fit={r['fitness']:.3f} "
                          f"density={r['density']:.2f} "
                          f"territory={r['territory']:4d}"
                          f"{conway_tag}")
                print()

    if verbose:
        # Final state
        print("═══ FINAL UNIVERSE ═══")
        # Show a cropped view
        view_h = min(24, height)
        view_w = min(48, width)
        for y in range(view_h):
            line = ''
            for x in range(view_w):
                line += '█' if grid.cells[y][x] else '·'
            print(f"  {line}")
        print()

        # Lineage analysis
        print("═══ EVOLUTIONARY LINEAGE ═══")
        for r in grid.rules:
            lineage = f"gen {r.generation}"
            if r.parent_id:
                lineage += f" (from {r.parent_id})"
            print(f"  Rule {r.id}: {lineage}, {r.mutations} mutations, "
                  f"sig={r.signature()[:10]}...")

        # Did anything interesting emerge?
        print()
        print("═══ EMERGENCE REPORT ═══")
        unique_sigs = set(r.signature() for r in grid.rules)
        max_gen = max(r.generation for r in grid.rules)
        print(f"  Unique rule phenotypes: {len(unique_sigs)}/{len(grid.rules)}")
        print(f"  Maximum generation depth: {max_gen}")
        print(f"  Conway's Life discovered: {any(r.is_conway() for r in grid.rules)}")

        # Check for dominant rule
        territory_counts = Counter()
        for row in grid.territories:
            territory_counts.update(row)
        dominant = territory_counts.most_common(1)[0]
        dominant_rule = grid.rules[dominant[0]]
        total = width * height
        print(f"  Dominant rule: {dominant_rule.id} "
              f"({dominant[1]/total*100:.1f}% of territory)")

    return grid


if __name__ == '__main__':
    grid = run_universe(
        steps=300,
        evolve_every=30,
        width=48,
        height=32,
        n_rules=6,
        verbose=True,
    )