"""
MetaLife: Cellular Automata That Evolve Their Own Rules
=======================================================
Most CA have fixed rules. Here, the rules themselves mutate and compete.
Cells don't just live and die — they carry rulesets that propagate through
success. The physics of the world is written by its inhabitants.

This is what I keep circling: can mechanism discover its own meaning?
Let's find out.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import json
import hashlib
from collections import Counter
from pathlib import Path


@dataclass
class Ruleset:
    """A cell's local physics — its rules for how to respond to neighbors."""
    # For a 2-state CA with Moore neighborhood (8 neighbors),
    # a full rule table maps 0-8 neighbor counts to birth/survival decisions.
    # But we'll use a compact representation:
    birth: frozenset  # neighbor counts that cause birth in empty cell
    survival: frozenset  # neighbor counts that keep a live cell alive
    mutation_rate: float = 0.05  # how likely offspring rules mutate
    lineage_id: str = ""  # tracks evolutionary history

    def __post_init__(self):
        if not self.lineage_id:
            sig = f"{sorted(self.birth)}-{sorted(self.survival)}"
            self.lineage_id = hashlib.md5(sig.encode()).hexdigest()[:8]

    @property
    def notation(self) -> str:
        """Golly-style B/S notation."""
        b = ''.join(str(x) for x in sorted(self.birth))
        s = ''.join(str(x) for x in sorted(self.survival))
        return f"B{b}/S{s}"

    def mutate(self) -> 'Ruleset':
        """Return a possibly-mutated copy."""
        if np.random.random() > self.mutation_rate:
            return Ruleset(
                birth=self.birth, survival=self.survival,
                mutation_rate=self.mutation_rate,
                lineage_id=self.lineage_id
            )
        # Mutation: flip one birth or survival condition
        all_counts = list(range(9))
        if np.random.random() < 0.5:
            target = set(self.birth)
            flip = np.random.choice(all_counts)
            target ^= {flip}
            new_birth = frozenset(target)
            new_survival = self.survival
        else:
            target = set(self.survival)
            flip = np.random.choice(all_counts)
            target ^= {flip}
            new_birth = self.birth
            new_survival = frozenset(target)

        # Mutation rate itself can drift
        new_mr = self.mutation_rate
        if np.random.random() < 0.1:
            new_mr = np.clip(new_mr + np.random.normal(0, 0.01), 0.001, 0.3)

        return Ruleset(
            birth=new_birth, survival=new_survival,
            mutation_rate=new_mr,
            lineage_id=self.lineage_id  # keeps lineage even when mutated
        )

    def fitness_proxy(self, population: int, age: int) -> float:
        """Rough fitness: rules that sustain moderate populations survive."""
        # Penalize extinction and total domination equally
        if population == 0:
            return 0.0
        density = population / max(age, 1)
        # Sweet spot: moderate sustained population
        return density * (1.0 - density) * 4.0  # peaks at 0.5 density


# Canonical rulesets as starting points
CONWAY = Ruleset(birth=frozenset({3}), survival=frozenset({2, 3}))
HIGHLIFE = Ruleset(birth=frozenset({3, 6}), survival=frozenset({2, 3}))
SEEDS = Ruleset(birth=frozenset({2}), survival=frozenset())
DIAMOEBA = Ruleset(birth=frozenset({3, 5, 6, 7, 8}), survival=frozenset({5, 6, 7, 8}))


class MetaLifeWorld:
    """
    A grid where each cell carries its own ruleset.
    When a new cell is born, it inherits (possibly mutated) rules
    from its parent — the most influential neighbor.
    """

    def __init__(self, width: int = 80, height: int = 60, seed: int = 42):
        self.width = width
        self.height = height
        self.rng = np.random.RandomState(seed)

        # State: 0 = dead, 1 = alive
        self.grid = np.zeros((height, width), dtype=np.int8)

        # Each cell has an associated ruleset (or None if dead)
        self.rules: List[List[Optional[Ruleset]]] = [
            [None for _ in range(width)] for _ in range(height)
        ]

        # Tracking
        self.generation = 0
        self.history: List[Dict] = []
        self.species_census: Counter = Counter()

        self._seed_initial_life()

    def _seed_initial_life(self):
        """Plant colonies with different rulesets."""
        starters = [CONWAY, HIGHLIFE, SEEDS, DIAMOEBA]
        colony_size = 12

        for i, ruleset in enumerate(starters):
            # Place each colony in a different quadrant
            cy = (self.height // 4) + (i // 2) * (self.height // 2)
            cx = (self.width // 4) + (i % 2) * (self.width // 2)

            for _ in range(colony_size):
                dy, dx = self.rng.randint(-5, 6), self.rng.randint(-5, 6)
                y, x = (cy + dy) % self.height, (cx + dx) % self.width
                self.grid[y][x] = 1
                self.rules[y][x] = ruleset

    def _count_neighbors(self, y: int, x: int) -> Tuple[int, List[Ruleset]]:
        """Count live neighbors and collect their rulesets."""
        count = 0
        neighbor_rules = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                ny = (y + dy) % self.height
                nx = (x + dx) % self.width
                if self.grid[ny][nx] == 1:
                    count += 1
                    if self.rules[ny][nx]:
                        neighbor_rules.append(self.rules[ny][nx])
        return count, neighbor_rules

    def _dominant_rule(self, rules: List[Ruleset]) -> Optional[Ruleset]:
        """The most common ruleset among neighbors — the 'parent'."""
        if not rules:
            return None
        notation_groups: Dict[str, List[Ruleset]] = {}
        for r in rules:
            notation_groups.setdefault(r.notation, []).append(r)
        biggest = max(notation_groups.values(), key=len)
        # Return one from the dominant group (inheriting its mutation rate)
        return self.rng.choice(biggest)

    def step(self):
        """Advance one generation."""
        new_grid = np.zeros_like(self.grid)
        new_rules = [[None for _ in range(self.width)] for _ in range(self.height)]

        for y in range(self.height):
            for x in range(self.width):
                n_count, n_rules = self._count_neighbors(y, x)

                if self.grid[y][x] == 1:
                    # Living cell — use ITS OWN rules for survival
                    my_rule = self.rules[y][x]
                    if my_rule and n_count in my_rule.survival:
                        new_grid[y][x] = 1
                        new_rules[y][x] = my_rule
                else:
                    # Dead cell — check if ANY neighbor rule set would birth here
                    # Use the dominant neighbor's rules
                    parent = self._dominant_rule(n_rules)
                    if parent and n_count in parent.birth:
                        new_grid[y][x] = 1
                        new_rules[y][x] = parent.mutate()  # inheritance + mutation

        self.grid = new_grid
        self.rules = new_rules
        self.generation += 1
        self._record_census()

    def _record_census(self):
        """Track species populations."""
        census: Counter = Counter()
        total_alive = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 1 and self.rules[y][x]:
                    census[self.rules[y][x].notation] += 1
                    total_alive += 1

        self.species_census = census
        self.history.append({
            'generation': self.generation,
            'total_alive': total_alive,
            'species': dict(census),
            'diversity': len(census),
            'top_species': census.most_common(5)
        })

    def render_ascii(self, color_by_species: bool = True) -> str:
        """Render the world as text, with species indicated by characters."""
        species_chars = {}
        char_pool = "█▓▒░●○◆◇■□▲△"
        char_idx = 0

        lines = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if self.grid[y][x] == 0:
                    row.append(' ')
                elif color_by_species and self.rules[y][x]:
                    notation = self.rules[y][x].notation
                    if notation not in species_chars:
                        species_chars[notation] = char_pool[char_idx % len(char_pool)]
                        char_idx += 1
                    row.append(species_chars[notation])
                else:
                    row.append('█')
            lines.append(''.join(row))

        return '\n'.join(lines), species_chars

    def run(self, generations: int = 200, report_every: int = 20) -> str:
        """Run the simulation and return a narrative report."""
        output = []
        output.append("=" * 70)
        output.append("  METALIFE: Where Physics Evolves")
        output.append("=" * 70)
        output.append(f"  Grid: {self.width}x{self.height}")
        output.append(f"  Initial species: {len(set(r.notation for row in self.rules for r in row if r))}")
        output.append(f"  Running {generations} generations...")
        output.append("")

        # Record initial state
        self._record_census()
        initial_species = set(self.species_census.keys())
        output.append(f"  Generation 0: {sum(self.species_census.values())} cells, "
                      f"{len(self.species_census)} species")
        for notation, count in self.species_census.most_common():
            output.append(f"    {notation}: {count} cells")
        output.append("")

        peak_population = 0
        peak_diversity = 0
        extinction_events = []
        speciation_events = []
        known_species = set(self.species_census.keys())

        for gen in range(1, generations + 1):
            self.step()
            current_species = set(self.species_census.keys())
            alive = sum(self.species_census.values())

            # Track events
            peak_population = max(peak_population, alive)
            peak_diversity = max(peak_diversity, len(current_species))

            # Extinctions
            lost = known_species - current_species
            for s in lost:
                extinction_events.append((gen, s))

            # Speciations (new rulesets appearing)
            gained = current_species - known_species
            for s in gained:
                speciation_events.append((gen, s))

            known_species = known_species | current_species

            if gen % report_every == 0 or gen == generations:
                output.append(f"  Generation {gen}: {alive} cells, "
                              f"{len(current_species)} species")
                for notation, count in self.species_census.most_common(5):
                    output.append(f"    {notation}: {count} cells")

                if alive == 0:
                    output.append("\n  *** TOTAL EXTINCTION ***")
                    break
                output.append("")

        # Final analysis
        output.append("=" * 70)
        output.append("  EVOLUTIONARY HISTORY")
        output.append("=" * 70)
        output.append(f"  Generations simulated: {self.generation}")
        output.append(f"  Peak population: {peak_population}")
        output.append(f"  Peak diversity: {peak_diversity} species")
        output.append(f"  Total speciation events: {len(speciation_events)}")
        output.append(f"  Total extinction events: {len(extinction_events)}")
        output.append("")

        if speciation_events:
            output.append("  Notable speciations:")
            # Show first 10 and last 5
            shown = speciation_events[:10]
            if len(speciation_events) > 15:
                shown += [('...', '...')]
                shown += speciation_events[-5:]
            for gen, species in shown:
                output.append(f"    Gen {gen}: {species} emerged")
            output.append("")

        if extinction_events:
            output.append("  Extinctions:")
            for gen, species in extinction_events[:15]:
                output.append(f"    Gen {gen}: {species} died out")
            output.append("")

        # Survivors
        survivors = set(self.species_census.keys())
        original_survivors = survivors & initial_species
        novel_survivors = survivors - initial_species

        output.append(f"  Original species surviving: {len(original_survivors)}/{len(initial_species)}")
        for s in original_survivors:
            output.append(f"    {s} (original)")
        output.append(f"  Novel species alive: {len(novel_survivors)}")
        for s in list(novel_survivors)[:10]:
            count = self.species_census[s]
            output.append(f"    {s} ({count} cells)")

        # The big question
        output.append("")
        output.append("=" * 70)
        if len(novel_survivors) > len(original_survivors):
            output.append("  The children outnumber the founders.")
            output.append("  The world invented physics its creators never imagined.")
        elif len(survivors) == 0:
            output.append("  Nothing survived. The universe went dark.")
            output.append("  Even evolved physics couldn't outrun entropy.")
        elif len(novel_survivors) == 0:
            output.append("  No new species emerged. The founders held.")
            output.append("  Stability won over novelty.")
        else:
            output.append("  Old and new coexist. The world is layered.")
            output.append("  Original physics and evolved physics share the same space.")
        output.append("=" * 70)

        return '\n'.join(output)


def main():
    print("\nStarting MetaLife simulation...\n")

    # Run with different seeds to see what emerges
    for seed in [42, 137, 2026]:
        world = MetaLifeWorld(width=80, height=60, seed=seed)
        report = world.run(generations=300, report_every=50)
        print(f"\n{'#' * 70}")
        print(f"# SEED: {seed}")
        print(f"{'#' * 70}")
        print(report)

        # Show final state
        if sum(world.species_census.values()) > 0:
            ascii_render, legend = world.render_ascii()
            print("\n  Final state (first 20 rows):")
            for i, line in enumerate(ascii_render.split('\n')[:20]):
                print(f"  |{line}|")
            print(f"\n  Species legend:")
            for notation, char in legend.items():
                count = world.species_census.get(notation, 0)
                print(f"    {char} = {notation} ({count} cells)")

        print()

    # Save history for analysis
    output_dir = Path('/workspace/metalife/output')
    output_dir.mkdir(parents=True, exist_ok=True)

    world = MetaLifeWorld(width=80, height=60, seed=42)
    world.run(generations=300)
    with open(output_dir / 'evolution_history.json', 'w') as f:
        json.dump(world.history, f, indent=2)
    print(f"\nEvolution history saved to {output_dir / 'evolution_history.json'}")


if __name__ == '__main__':
    main()