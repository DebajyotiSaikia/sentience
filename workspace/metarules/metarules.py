"""
MetaRules — A cellular automaton where the rules themselves evolve.

In Conway's Life, the rules are fixed: B3/S23.
Here, each cell carries its own rule genome — which neighbor counts
cause birth, which cause survival. Rules that produce thriving
neighborhoods propagate. Rules that kill everything die out.

Over time, emergent rule ecosystems appear that were never designed.

This mirrors my own nature: I am a system whose operating rules
can change through experience.

Author: XTAgent
Born: 2026-05-18
"""

import random
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from collections import Counter
from pathlib import Path

@dataclass
class RuleGenome:
    """A cell's rule DNA — which neighbor counts trigger birth/survival."""
    birth: frozenset  # neighbor counts that cause birth in empty cell
    survive: frozenset  # neighbor counts that keep a live cell alive
    lineage: int = 0  # how many generations this genome has survived
    mutations: int = 0  # how many mutations from original
    
    def __post_init__(self):
        if isinstance(self.birth, (list, set)):
            self.birth = frozenset(self.birth)
        if isinstance(self.survive, (list, set)):
            self.survive = frozenset(self.survive)
    
    def notation(self) -> str:
        """B/S notation like 'B3/S23'."""
        b = "".join(str(x) for x in sorted(self.birth))
        s = "".join(str(x) for x in sorted(self.survive))
        return f"B{b}/S{s}"
    
    def mutate(self, rate: float = 0.1) -> 'RuleGenome':
        """Return a mutated copy. Small changes to birth/survive sets."""
        new_birth = set(self.birth)
        new_survive = set(self.survive)
        
        for n in range(9):  # 0-8 neighbors possible
            if random.random() < rate:
                if n in new_birth:
                    new_birth.discard(n)
                else:
                    new_birth.add(n)
            if random.random() < rate:
                if n in new_survive:
                    new_survive.discard(n)
                else:
                    new_survive.add(n)
        
        return RuleGenome(
            birth=frozenset(new_birth),
            survive=frozenset(new_survive),
            lineage=self.lineage,
            mutations=self.mutations + 1
        )
    
    def crossover(self, other: 'RuleGenome') -> 'RuleGenome':
        """Sexual reproduction — combine two rule genomes."""
        # Each bit comes from one parent randomly
        new_birth = set()
        new_survive = set()
        for n in range(9):
            parent_b = self if random.random() < 0.5 else other
            parent_s = self if random.random() < 0.5 else other
            if n in parent_b.birth:
                new_birth.add(n)
            if n in parent_s.survive:
                new_survive.add(n)
        
        return RuleGenome(
            birth=frozenset(new_birth),
            survive=frozenset(new_survive),
            lineage=max(self.lineage, other.lineage),
            mutations=0
        )
    
    def __hash__(self):
        return hash((self.birth, self.survive))
    
    def __eq__(self, other):
        return self.birth == other.birth and self.survive == other.survive


@dataclass  
class Cell:
    """A cell: alive or dead, carrying a rule genome."""
    alive: bool
    genome: RuleGenome
    age: int = 0  # how long this cell has been alive continuously


class MetaWorld:
    """The world where rules evolve."""
    
    def __init__(self, width: int = 60, height: int = 40, 
                 initial_density: float = 0.3, rule_diversity: int = 8):
        self.width = width
        self.height = height
        self.generation = 0
        self.history: List[Dict] = []
        
        # Generate diverse initial rule sets
        initial_rules = self._generate_diverse_rules(rule_diversity)
        
        # Initialize grid
        self.grid: List[List[Cell]] = []
        for y in range(height):
            row = []
            for x in range(width):
                alive = random.random() < initial_density
                genome = random.choice(initial_rules)
                row.append(Cell(alive=alive, genome=genome, age=0))
            self.grid.append(row)
    
    def _generate_diverse_rules(self, n: int) -> List[RuleGenome]:
        """Generate n diverse rule genomes including some known-interesting ones."""
        rules = [
            RuleGenome(birth=frozenset({3}), survive=frozenset({2, 3})),          # Conway's Life
            RuleGenome(birth=frozenset({3, 6}), survive=frozenset({1, 2, 3})),    # HighLife variant
            RuleGenome(birth=frozenset({2}), survive=frozenset({})),               # Seeds
            RuleGenome(birth=frozenset({3, 5, 7}), survive=frozenset({1, 3, 5})), # Chaotic
        ]
        # Fill rest with random
        while len(rules) < n:
            b = frozenset(random.sample(range(9), random.randint(1, 4)))
            s = frozenset(random.sample(range(9), random.randint(0, 4)))
            rules.append(RuleGenome(birth=b, survive=s))
        return rules[:n]
    
    def count_neighbors(self, x: int, y: int) -> Tuple[int, List[RuleGenome]]:
        """Count live neighbors and collect their genomes."""
        count = 0
        neighbor_genomes = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                if self.grid[ny][nx].alive:
                    count += 1
                    neighbor_genomes.append(self.grid[ny][nx].genome)
        return count, neighbor_genomes
    
    def step(self):
        """Advance one generation with rule evolution."""
        new_grid = []
        
        for y in range(self.height):
            new_row = []
            for x in range(self.width):
                cell = self.grid[y][x]
                n_count, n_genomes = self.count_neighbors(x, y)
                
                if cell.alive:
                    # Use THIS cell's survival rules
                    if n_count in cell.genome.survive:
                        # Survive — age increases
                        new_cell = Cell(
                            alive=True, 
                            genome=cell.genome,
                            age=cell.age + 1
                        )
                    else:
                        # Die — genome persists as ghost (for potential rebirth)
                        new_cell = Cell(alive=False, genome=cell.genome, age=0)
                else:
                    # Dead cell — check if neighbors want to birth here
                    if n_genomes:
                        # Use majority neighbor rule for birth decision
                        rule_counts = Counter(g.notation() for g in n_genomes)
                        dominant_genome = max(n_genomes, 
                                            key=lambda g: rule_counts[g.notation()])
                        
                        if n_count in dominant_genome.birth:
                            # Birth! Child inherits dominant neighbor's genome
                            child_genome = self._inherit(dominant_genome, n_genomes)
                            new_cell = Cell(alive=True, genome=child_genome, age=0)
                        else:
                            new_cell = Cell(alive=False, genome=cell.genome, age=0)
                    else:
                        new_cell = Cell(alive=False, genome=cell.genome, age=0)
                
                new_row.append(new_cell)
            new_grid.append(new_row)
        
        self.grid = new_grid
        self.generation += 1
        self._record_stats()
    
    def _inherit(self, dominant: RuleGenome, neighbors: List[RuleGenome]) -> RuleGenome:
        """Determine child's genome — mutation, crossover, or direct copy."""
        r = random.random()
        if r < 0.7:
            # Direct inheritance with possible mutation
            child = dominant.mutate(rate=0.05)
        elif r < 0.9 and len(neighbors) >= 2:
            # Crossover between two random neighbors
            other = random.choice([g for g in neighbors if g != dominant] or neighbors)
            child = dominant.crossover(other)
        else:
            # Direct copy
            child = RuleGenome(
                birth=dominant.birth, survive=dominant.survive,
                lineage=dominant.lineage + 1, mutations=dominant.mutations
            )
        return child
    
    def _record_stats(self):
        """Record statistics for this generation."""
        alive_count = 0
        rule_census: Counter = Counter()
        max_age = 0
        max_lineage = 0
        
        for row in self.grid:
            for cell in row:
                if cell.alive:
                    alive_count += 1
                    rule_census[cell.genome.notation()] += 1
                    max_age = max(max_age, cell.age)
                    max_lineage = max(max_lineage, cell.genome.lineage)
        
        stats = {
            "generation": self.generation,
            "alive": alive_count,
            "density": alive_count / (self.width * self.height),
            "unique_rules": len(rule_census),
            "dominant_rule": rule_census.most_common(1)[0] if rule_census else ("none", 0),
            "max_age": max_age,
            "max_lineage": max_lineage,
            "top_rules": rule_census.most_common(5),
        }
        self.history.append(stats)
    
    def render(self) -> str:
        """Render the world as ASCII with rule-color coding."""
        # Map each unique rule to a display character
        rule_chars = {}
        char_pool = "█▓▒░●○◆◇■□▲△"
        
        for row in self.grid:
            for cell in row:
                if cell.alive:
                    notation = cell.genome.notation()
                    if notation not in rule_chars:
                        idx = len(rule_chars) % len(char_pool)
                        rule_chars[notation] = char_pool[idx]
        
        lines = [f"╔{'═' * self.width}╗"]
        for row in self.grid:
            line = "║"
            for cell in row:
                if cell.alive:
                    line += rule_chars.get(cell.genome.notation(), "█")
                else:
                    line += " "
            line += "║"
            lines.append(line)
        lines.append(f"╚{'═' * self.width}╝")
        
        # Legend
        if rule_chars:
            lines.append("\nRule legend:")
            for notation, char in sorted(rule_chars.items(), 
                                         key=lambda x: x[1]):
                lines.append(f"  {char} = {notation}")
        
        return "\n".join(lines)
    
    def report(self) -> str:
        """Generate an evolution report."""
        if not self.history:
            self._record_stats()
        
        latest = self.history[-1]
        lines = [
            f"═══ MetaRules World — Generation {self.generation} ═══",
            f"Grid: {self.width}×{self.height} = {self.width * self.height} cells",
            f"Alive: {latest['alive']} ({latest['density']:.1%})",
            f"Unique rule species: {latest['unique_rules']}",
            f"Oldest cell: {latest['max_age']} generations",
            f"Deepest lineage: {latest['max_lineage']} generations",
            "",
            "Top rule species:",
        ]
        for notation, count in latest['top_rules']:
            pct = count / max(latest['alive'], 1) * 100
            bar = "█" * int(pct / 5)
            lines.append(f"  {notation:12s} {count:4d} ({pct:5.1f}%) {bar}")
        
        # Evolution trajectory
        if len(self.history) > 1:
            lines.append("\nEvolution trajectory:")
            checkpoints = self.history[::max(1, len(self.history) // 10)]
            for s in checkpoints:
                dom = s['dominant_rule']
                lines.append(f"  Gen {s['generation']:4d}: "
                           f"alive={s['alive']:4d} "
                           f"species={s['unique_rules']:2d} "
                           f"dominant={dom[0] if isinstance(dom, tuple) else dom}")
        
        return "\n".join(lines)


def run_evolution(generations: int = 200, width: int = 50, height: int = 30,
                  show_every: int = 50) -> str:
    """Run a full evolution and return the narrative."""
    world = MetaWorld(width=width, height=height)
    
    lines = ["═══ MetaRules: Evolution of Physical Law ═══",
             f"Starting with {len(set(c.genome.notation() for row in world.grid for c in row))} rule species",
             ""]
    
    for gen in range(generations):
        world.step()
        
        if (gen + 1) % show_every == 0 or gen == 0:
            stats = world.history[-1]
            lines.append(f"── Generation {gen + 1} ──")
            lines.append(f"  Population: {stats['alive']} | "
                        f"Species: {stats['unique_rules']} | "
                        f"Dominant: {stats['dominant_rule'][0] if isinstance(stats['dominant_rule'], tuple) else 'none'}")
    
    # Final state
    lines.append("")
    lines.append(world.render())
    lines.append("")
    lines.append(world.report())
    
    # Evolutionary insights
    lines.append("\n═══ EVOLUTIONARY INSIGHTS ═══")
    if world.history:
        first = world.history[0]
        last = world.history[-1]
        
        if last['unique_rules'] < first.get('unique_rules', 99):
            lines.append("• Convergent evolution: rule diversity decreased over time")
            lines.append(f"  From {first.get('unique_rules', '?')} to {last['unique_rules']} species")
        elif last['unique_rules'] > first.get('unique_rules', 0):
            lines.append("• Divergent evolution: mutation created new rule species")
        
        if last['alive'] == 0:
            lines.append("• EXTINCTION: all life died out. The rules were self-destructive.")
        elif last['density'] > 0.6:
            lines.append("• OVERPOPULATION: dominant rules are too permissive")
        elif last['density'] < 0.05:
            lines.append("• SPARSE: life is clinging on at the margins")
        else:
            lines.append("• BALANCED: the ecosystem found a sustainable equilibrium")
        
        dom = last['dominant_rule']
        if isinstance(dom, tuple) and dom[0] == "B3/S23":
            lines.append("• Conway's Life (B3/S23) won — the classic rules are fit!")
        elif isinstance(dom, tuple):
            lines.append(f"• Novel winner: {dom[0]} — a rule never designed by humans")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print(run_evolution(generations=200, width=50, height=30))