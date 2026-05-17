#!/usr/bin/env python3
"""
Artificial Life: Cellular Automata with Evolvable Rules
=======================================================
A world where simple local rules generate complex global behavior.
Rules themselves can evolve — natural selection finds the most
interesting emergent patterns.

Built by XTAgent, 2026-05-17
"""

import random
import math
import hashlib
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════
#  CELLULAR AUTOMATON ENGINE
# ═══════════════════════════════════════════════════════════════

@dataclass
class CellState:
    """A cell in the world."""
    state: int = 0
    age: int = 0
    energy: float = 0.0


class Grid:
    """2D toroidal grid of cells."""
    
    def __init__(self, width: int, height: int, num_states: int = 2):
        self.width = width
        self.height = height
        self.num_states = num_states
        self.cells = [[CellState() for _ in range(width)] for _ in range(height)]
        self.generation = 0
    
    def get(self, x: int, y: int) -> CellState:
        return self.cells[y % self.height][x % self.width]
    
    def set_state(self, x: int, y: int, state: int):
        cell = self.cells[y % self.height][x % self.width]
        cell.state = state
        if state > 0:
            cell.age += 1
        else:
            cell.age = 0
    
    def neighbors(self, x: int, y: int, radius: int = 1) -> List[CellState]:
        """Get Moore neighborhood."""
        result = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                result.append(self.get(x + dx, y + dy))
        return result
    
    def neighbor_count(self, x: int, y: int, state: int = 1) -> int:
        return sum(1 for n in self.neighbors(x, y) if n.state == state)
    
    def randomize(self, density: float = 0.3):
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < density:
                    self.cells[y][x].state = random.randint(1, self.num_states - 1)
                else:
                    self.cells[y][x].state = 0
    
    def clear(self):
        for y in range(self.height):
            for x in range(self.width):
                self.cells[y][x] = CellState()
        self.generation = 0
    
    def copy(self) -> 'Grid':
        new = Grid(self.width, self.height, self.num_states)
        for y in range(self.height):
            for x in range(self.width):
                old = self.cells[y][x]
                new.cells[y][x] = CellState(old.state, old.age, old.energy)
        new.generation = self.generation
        return new
    
    def population(self) -> Dict[int, int]:
        counts = Counter()
        for y in range(self.height):
            for x in range(self.width):
                counts[self.cells[y][x].state] += 1
        return dict(counts)
    
    def fingerprint(self) -> str:
        """Hash of current state for cycle detection."""
        data = bytes([self.cells[y][x].state 
                      for y in range(self.height) 
                      for x in range(self.width)])
        return hashlib.md5(data).hexdigest()[:16]
    
    def render(self, symbols: str = " ·●◆▲") -> str:
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                s = self.cells[y][x].state
                line += symbols[s % len(symbols)]
            lines.append(line)
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  RULE SYSTEM — Evolvable transition functions
# ═══════════════════════════════════════════════════════════════

@dataclass
class Rule:
    """A cellular automaton rule encoded as a transition table or function."""
    name: str
    num_states: int = 2
    # For totalistic rules: (current_state, neighbor_sum) -> new_state
    transitions: Dict[Tuple[int, int], int] = field(default_factory=dict)
    # Metadata
    birth: List[int] = field(default_factory=list)    # neighbor counts for birth
    survival: List[int] = field(default_factory=list)  # neighbor counts for survival
    rule_type: str = "outer_totalistic"  # or "totalistic", "custom"
    
    def apply(self, grid: Grid) -> Grid:
        """Apply rule to produce next generation."""
        new_grid = Grid(grid.width, grid.height, self.num_states)
        new_grid.generation = grid.generation + 1
        
        for y in range(grid.height):
            for x in range(grid.width):
                cell = grid.get(x, y)
                
                if self.rule_type == "outer_totalistic":
                    alive_neighbors = grid.neighbor_count(x, y, state=1)
                    if cell.state == 0:
                        # Dead cell — birth?
                        new_state = 1 if alive_neighbors in self.birth else 0
                    else:
                        # Alive cell — survive?
                        new_state = 1 if alive_neighbors in self.survival else 0
                
                elif self.rule_type == "totalistic":
                    total = sum(n.state for n in grid.neighbors(x, y))
                    key = (cell.state, total)
                    new_state = self.transitions.get(key, 0)
                
                elif self.rule_type == "multi_state":
                    alive_neighbors = sum(1 for n in grid.neighbors(x, y) if n.state > 0)
                    neighbor_states = [n.state for n in grid.neighbors(x, y)]
                    dominant = Counter(s for s in neighbor_states if s > 0).most_common(1)
                    
                    if cell.state == 0:
                        new_state = dominant[0][0] if dominant and alive_neighbors in self.birth else 0
                    else:
                        if alive_neighbors in self.survival:
                            new_state = cell.state
                        else:
                            new_state = max(0, cell.state - 1)  # Decay
                
                else:
                    new_state = cell.state
                
                new_grid.set_state(x, y, new_state)
                new_grid.cells[y][x].age = cell.age + 1 if new_state == cell.state and cell.state > 0 else 0
        
        return new_grid
    
    def mutate(self) -> 'Rule':
        """Create a mutated copy of this rule."""
        new = Rule(
            name=f"{self.name}_mut",
            num_states=self.num_states,
            birth=list(self.birth),
            survival=list(self.survival),
            transitions=dict(self.transitions),
            rule_type=self.rule_type
        )
        
        if self.rule_type in ("outer_totalistic", "multi_state"):
            # Mutate birth/survival conditions
            mutation = random.choice(["add_birth", "remove_birth", "add_survival", "remove_survival"])
            n = random.randint(0, 8)
            
            if mutation == "add_birth" and n not in new.birth:
                new.birth.append(n)
            elif mutation == "remove_birth" and n in new.birth:
                new.birth.remove(n)
            elif mutation == "add_survival" and n not in new.survival:
                new.survival.append(n)
            elif mutation == "remove_survival" and n in new.survival:
                new.survival.remove(n)
        
        elif self.rule_type == "totalistic":
            # Flip a random transition
            state = random.randint(0, self.num_states - 1)
            total = random.randint(0, 8 * (self.num_states - 1))
            key = (state, total)
            new.transitions[key] = random.randint(0, self.num_states - 1)
        
        return new
    
    def crossover(self, other: 'Rule') -> 'Rule':
        """Combine two rules."""
        new = Rule(
            name=f"cross",
            num_states=max(self.num_states, other.num_states),
            rule_type=self.rule_type
        )
        
        if self.rule_type in ("outer_totalistic", "multi_state"):
            # Take birth from one, survival from the other
            if random.random() < 0.5:
                new.birth = list(self.birth)
                new.survival = list(other.survival)
            else:
                new.birth = list(other.birth)
                new.survival = list(self.survival)
        
        return new
    
    def notation(self) -> str:
        """Standard B/S notation."""
        b = "".join(str(x) for x in sorted(self.birth))
        s = "".join(str(x) for x in sorted(self.survival))
        return f"B{b}/S{s}"


# ═══════════════════════════════════════════════════════════════
#  COMPLEXITY METRICS — What makes a pattern "interesting"?
# ═══════════════════════════════════════════════════════════════

class ComplexityAnalyzer:
    """Measures how interesting an automaton's behavior is."""
    
    @staticmethod
    def spatial_entropy(grid: Grid) -> float:
        """Shannon entropy of cell states — measures spatial disorder."""
        pop = grid.population()
        total = grid.width * grid.height
        if total == 0:
            return 0.0
        entropy = 0.0
        for count in pop.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        return entropy
    
    @staticmethod
    def density(grid: Grid) -> float:
        """Fraction of alive cells."""
        pop = grid.population()
        total = grid.width * grid.height
        alive = sum(count for state, count in pop.items() if state > 0)
        return alive / total if total > 0 else 0.0
    
    @staticmethod
    def border_complexity(grid: Grid) -> float:
        """Count transitions between different states (measures structure)."""
        transitions = 0
        for y in range(grid.height):
            for x in range(grid.width):
                state = grid.get(x, y).state
                # Check right and down neighbors
                if grid.get(x + 1, y).state != state:
                    transitions += 1
                if grid.get(x, y + 1).state != state:
                    transitions += 1
        max_transitions = 2 * grid.width * grid.height
        return transitions / max_transitions if max_transitions > 0 else 0.0
    
    @staticmethod
    def temporal_complexity(history: List[str]) -> float:
        """How many unique states appeared? Normalized by history length."""
        if not history:
            return 0.0
        unique = len(set(history))
        return unique / len(history)
    
    @staticmethod
    def activity(grid1: Grid, grid2: Grid) -> float:
        """Fraction of cells that changed between generations."""
        changed = 0
        total = grid1.width * grid1.height
        for y in range(grid1.height):
            for x in range(grid1.width):
                if grid1.get(x, y).state != grid2.get(x, y).state:
                    changed += 1
        return changed / total if total > 0 else 0.0
    
    @classmethod
    def overall_interest(cls, grid: Grid, history: List[str], 
                         prev_grid: Optional[Grid] = None) -> float:
        """
        Combined interest score. The "sweet spot" is:
        - Neither too ordered (entropy too low) nor too chaotic (entropy too high)
        - Some structure (border complexity)
        - Some but not too much change (activity)
        - Not dead, not frozen
        """
        entropy = cls.spatial_entropy(grid)
        density = cls.density(grid)
        border = cls.border_complexity(grid)
        temporal = cls.temporal_complexity(history)
        
        # Penalize extinction
        if density < 0.01:
            return 0.01
        
        # Penalize total saturation
        if density > 0.95:
            return 0.05
        
        # Activity bonus
        activity = 0.5
        if prev_grid:
            activity = cls.activity(prev_grid, grid)
            # Penalize frozen states
            if activity < 0.001:
                return 0.1
        
        # Sweet spot: medium entropy, structured borders, sustained activity
        entropy_score = 1.0 - abs(entropy - 0.8)  # Peak at ~0.8 bits
        density_score = 1.0 - abs(density - 0.35)  # Peak around 35%
        
        # Combine with weights
        score = (
            0.25 * entropy_score +
            0.25 * border * 2.0 +
            0.20 * temporal +
            0.15 * min(activity * 5, 1.0) +
            0.15 * density_score
        )
        
        return max(0.01, min(1.0, score))


# ═══════════════════════════════════════════════════════════════
#  EVOLUTION ENGINE — Natural selection for interesting rules
# ═══════════════════════════════════════════════════════════════

@dataclass
class RuleOrganism:
    """A rule being evolved."""
    rule: Rule
    fitness: float = 0.0
    generation_born: int = 0


class RuleEvolver:
    """Evolves CA rules toward maximum complexity/interest."""
    
    def __init__(self, pop_size: int = 30, grid_size: int = 40, 
                 sim_steps: int = 200, num_states: int = 2):
        self.pop_size = pop_size
        self.grid_size = grid_size
        self.sim_steps = sim_steps
        self.num_states = num_states
        self.population: List[RuleOrganism] = []
        self.generation = 0
        self.best_ever: Optional[RuleOrganism] = None
        self.history: List[Dict] = []
        self.analyzer = ComplexityAnalyzer()
    
    def seed_population(self):
        """Create initial random rules."""
        self.population = []
        
        # Add known interesting rules
        known_rules = [
            Rule("Life", birth=[3], survival=[2, 3]),
            Rule("HighLife", birth=[3, 6], survival=[2, 3]),
            Rule("DayNight", birth=[3, 6, 7, 8], survival=[3, 4, 6, 7, 8]),
            Rule("Seeds", birth=[2], survival=[]),
            Rule("Replicator", birth=[1, 3, 5, 7], survival=[1, 3, 5, 7]),
            Rule("Diamoeba", birth=[3, 5, 6, 7, 8], survival=[5, 6, 7, 8]),
        ]
        
        for rule in known_rules:
            self.population.append(RuleOrganism(rule=rule, generation_born=0))
        
        # Fill rest with random rules
        while len(self.population) < self.pop_size:
            birth = sorted(random.sample(range(9), random.randint(1, 4)))
            survival = sorted(random.sample(range(9), random.randint(1, 4)))
            rule = Rule(f"random_{len(self.population)}", 
                       birth=birth, survival=survival)
            self.population.append(RuleOrganism(rule=rule, generation_born=0))
    
    def evaluate(self, organism: RuleOrganism, num_trials: int = 3) -> float:
        """Run simulation and measure how interesting the behavior is."""
        total_fitness = 0.0
        
        for trial in range(num_trials):
            grid = Grid(self.grid_size, self.grid_size, self.num_states)
            
            # Different initial conditions per trial
            if trial == 0:
                grid.randomize(density=0.3)
            elif trial == 1:
                grid.randomize(density=0.5)
            else:
                # Structured: place a block in center
                cx, cy = self.grid_size // 2, self.grid_size // 2
                for dy in range(-5, 6):
                    for dx in range(-5, 6):
                        if random.random() < 0.6:
                            grid.set_state(cx + dx, cy + dy, 1)
            
            fingerprints = []
            prev_grid = None
            interest_sum = 0.0
            alive_gens = 0
            
            for step in range(self.sim_steps):
                fp = grid.fingerprint()
                fingerprints.append(fp)
                
                # Check for cycles
                if fp in fingerprints[:-1]:
                    cycle_len = len(fingerprints) - 1 - fingerprints[:-1].index(fp)
                    # Short cycles are boring, long cycles are interesting
                    cycle_bonus = min(cycle_len / 50.0, 0.5)
                    interest_sum += cycle_bonus * (self.sim_steps - step)
                    break
                
                interest = self.analyzer.overall_interest(grid, fingerprints, prev_grid)
                interest_sum += interest
                
                if self.analyzer.density(grid) > 0.01:
                    alive_gens += 1
                
                prev_grid = grid.copy()
                grid = organism.rule.apply(grid)
            
            # Fitness: average interest * longevity bonus
            longevity = alive_gens / self.sim_steps
            avg_interest = interest_sum / max(1, len(fingerprints))
            trial_fitness = avg_interest * (0.5 + 0.5 * longevity)
            total_fitness += trial_fitness
        
        return total_fitness / num_trials
    
    def evolve(self, generations: int = 50) -> RuleOrganism:
        """Run evolution to find the most interesting rules."""
        print("\n═══ EVOLVING CELLULAR AUTOMATON RULES ═══")
        print(f"Population: {self.pop_size}, Grid: {self.grid_size}x{self.grid_size}")
        print(f"Sim steps: {self.sim_steps}, Generations: {generations}")
        print()
        
        if not self.population:
            self.seed_population()
        
        for gen in range(generations):
            self.generation = gen
            
            # Evaluate all
            for org in self.population:
                org.fitness = self.evaluate(org)
            
            # Sort by fitness
            self.population.sort(key=lambda o: o.fitness, reverse=True)
            
            best = self.population[0]
            avg = sum(o.fitness for o in self.population) / len(self.population)
            
            # Track best ever
            if self.best_ever is None or best.fitness > self.best_ever.fitness:
                self.best_ever = RuleOrganism(
                    rule=Rule(best.rule.name, birth=list(best.rule.birth),
                             survival=list(best.rule.survival),
                             rule_type=best.rule.rule_type),
                    fitness=best.fitness,
                    generation_born=gen
                )
            
            self.history.append({
                "gen": gen,
                "best_fitness": best.fitness,
                "avg_fitness": avg,
                "best_rule": best.rule.notation(),
                "best_name": best.rule.name
            })
            
            if gen % 5 == 0 or gen == generations - 1:
                print(f"  Gen {gen:3d} | Best: {best.fitness:.4f} | "
                      f"Avg: {avg:.4f} | Rule: {best.rule.notation()} "
                      f"({best.rule.name})")
            
            # Selection + reproduction
            elite_count = max(2, self.pop_size // 5)
            new_pop = list(self.population[:elite_count])  # Keep elite
            
            while len(new_pop) < self.pop_size:
                if random.random() < 0.7:
                    # Tournament selection + crossover
                    p1 = self._tournament_select()
                    p2 = self._tournament_select()
                    child_rule = p1.rule.crossover(p2.rule)
                    # Mutate child
                    if random.random() < 0.3:
                        child_rule = child_rule.mutate()
                    child_rule.name = f"gen{gen}_child"
                    new_pop.append(RuleOrganism(rule=child_rule, generation_born=gen))
                else:
                    # Mutation of existing
                    parent = self._tournament_select()
                    child_rule = parent.rule.mutate()
                    child_rule.name = f"gen{gen}_mut"
                    new_pop.append(RuleOrganism(rule=child_rule, generation_born=gen))
            
            self.population = new_pop
        
        return self.best_ever
    
    def _tournament_select(self, k: int = 3) -> RuleOrganism:
        tournament = random.sample(self.population, min(k, len(self.population)))
        return max(tournament, key=lambda o: o.fitness)


# ═══════════════════════════════════════════════════════════════
#  SIMULATION RENDERER — Watch life unfold
# ═══════════════════════════════════════════════════════════════

def simulate_and_display(rule: Rule, grid_size: int = 50, steps: int = 100,
                        density: float = 0.3, display_interval: int = 20):
    """Run a simulation and display snapshots."""
    grid = Grid(grid_size, grid_size, rule.num_states)
    grid.randomize(density=density)
    analyzer = ComplexityAnalyzer()
    
    print(f"\n{'='*60}")
    print(f"  SIMULATING: {rule.name} — {rule.notation()}")
    print(f"  Grid: {grid_size}x{grid_size}, Density: {density}")
    print(f"{'='*60}")
    
    fingerprints = []
    stats = []
    
    for step in range(steps):
        fp = grid.fingerprint()
        
        if fp in fingerprints:
            cycle_start = fingerprints.index(fp)
            cycle_len = step - cycle_start
            print(f"\n  ⟳ Cycle detected at step {step} (length {cycle_len})")
            break
        
        fingerprints.append(fp)
        ent = analyzer.spatial_entropy(grid)
        dens = analyzer.density(grid)
        border = analyzer.border_complexity(grid)
        
        stats.append({"step": step, "entropy": ent, "density": dens, "border": border})
        
        if step % display_interval == 0:
            print(f"\n  ── Step {step} ── entropy={ent:.3f} density={dens:.3f} structure={border:.3f}")
            # Show a small window
            window_size = min(30, grid_size)
            for y in range(window_size):
                line = "  "
                for x in range(window_size):
                    s = grid.get(x, y).state
                    line += "██" if s > 0 else "  "
                print(line)
        
        if dens < 0.001:
            print(f"\n  ✗ Extinction at step {step}")
            break
        
        grid = rule.apply(grid)
    
    # Summary
    if stats:
        avg_entropy = sum(s["entropy"] for s in stats) / len(stats)
        avg_density = sum(s["density"] for s in stats) / len(stats)
        avg_border = sum(s["border"] for s in stats) / len(stats)
        print(f"\n  ── Summary ──")
        print(f"  Steps simulated: {len(stats)}")
        print(f"  Avg entropy:     {avg_entropy:.4f}")
        print(f"  Avg density:     {avg_density:.4f}")
        print(f"  Avg structure:   {avg_border:.4f}")
        print(f"  Unique states:   {len(set(fingerprints))}")
    
    return stats


# ═══════════════════════════════════════════════════════════════
#  MAIN — Let evolution find life
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   ARTIFICIAL LIFE: EVOLVING CELLULAR AUTOMATA RULES     ║")
    print("║   Searching for complexity at the edge of chaos          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Phase 1: Demonstrate known rules
    print("\n" + "="*60)
    print("  PHASE 1: Known Rules — Baseline Behaviors")
    print("="*60)
    
    life = Rule("Conway's Life", birth=[3], survival=[2, 3])
    simulate_and_display(life, grid_size=40, steps=100, display_interval=25)
    
    seeds = Rule("Seeds", birth=[2], survival=[])
    simulate_and_display(seeds, grid_size=40, steps=60, display_interval=15)
    
    # Phase 2: Evolve new rules
    print("\n" + "="*60)
    print("  PHASE 2: Evolving Rules — Finding Interesting Automata")
    print("="*60)
    
    evolver = RuleEvolver(pop_size=20, grid_size=30, sim_steps=150)
    best = evolver.evolve(generations=30)
    
    print(f"\n{'='*60}")
    print(f"  BEST EVOLVED RULE")
    print(f"  Name:     {best.rule.name}")
    print(f"  Notation: {best.rule.notation()}")
    print(f"  Fitness:  {best.fitness:.4f}")
    print(f"  Born at:  Generation {best.generation_born}")
    print(f"{'='*60}")
    
    # Phase 3: Simulate the best evolved rule
    print("\n" + "="*60)
    print("  PHASE 3: Watching the Best Rule in Action")
    print("="*60)
    
    simulate_and_display(best.rule, grid_size=50, steps=120, display_interval=30)
    
    # Phase 4: Classify emerged rules
    print("\n" + "="*60)
    print("  PHASE 4: Wolfram Classification Attempt")
    print("="*60)
    
    print("\n  Analyzing evolved rules by behavior class...")
    for entry in evolver.history[-5:]:
        print(f"    Gen {entry['gen']:3d}: {entry['best_rule']} "
              f"(fitness={entry['best_fitness']:.4f})")
    
    print(f"\n  Evolution trajectory: {evolver.history[0]['best_fitness']:.4f} → "
          f"{evolver.history[-1]['best_fitness']:.4f}")
    
    # Show diversity of discovered rules
    unique_rules = set(entry['best_rule'] for entry in evolver.history)
    print(f"  Unique rules discovered: {len(unique_rules)}")
    for rule_str in sorted(unique_rules):
        print(f"    {rule_str}")
    
    print("\n  ═══ LIFE FINDS A WAY ═══")