#!/usr/bin/env python3
"""
Cellular Automaton Laboratory — XTAgent
Evolves cellular automaton rules that produce interesting emergent behavior.
Combines genetic search with pattern detection to find rules that create
gliders, oscillators, and complex dynamics from simple local interactions.
"""

import random
import math
from collections import defaultdict
from typing import List, Tuple, Dict, Set, Optional

# ═══════════════════════════════════════════════════
#  GRID — The world where cells live and die
# ═══════════════════════════════════════════════════

class Grid:
    """A 2D toroidal grid of binary cells."""
    
    def __init__(self, width: int, height: int, cells: Optional[List[List[int]]] = None):
        self.width = width
        self.height = height
        if cells:
            self.cells = [row[:] for row in cells]
        else:
            self.cells = [[0]*width for _ in range(height)]
    
    def randomize(self, density: float = 0.3):
        """Fill with random cells at given density."""
        for y in range(self.height):
            for x in range(self.width):
                self.cells[y][x] = 1 if random.random() < density else 0
    
    def copy(self) -> 'Grid':
        return Grid(self.width, self.height, self.cells)
    
    def count_alive(self) -> int:
        return sum(sum(row) for row in self.cells)
    
    def get(self, x: int, y: int) -> int:
        """Get cell with toroidal wrapping."""
        return self.cells[y % self.height][x % self.width]
    
    def set(self, x: int, y: int, val: int):
        self.cells[y % self.height][x % self.width] = val
    
    def neighbor_count(self, x: int, y: int) -> int:
        """Count Moore neighborhood (8 neighbors)."""
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                count += self.get(x + dx, y + dy)
        return count
    
    def fingerprint(self) -> int:
        """Hash the grid state for cycle detection."""
        h = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.cells[y][x]:
                    h ^= hash((x, y))
        return h
    
    def render(self) -> str:
        """ASCII render of the grid."""
        lines = []
        for row in self.cells:
            lines.append(''.join('█' if c else '·' for c in row))
        return '\n'.join(lines)
    
    def __eq__(self, other):
        if not isinstance(other, Grid):
            return False
        return self.cells == other.cells
    
    def __hash__(self):
        return self.fingerprint()


# ═══════════════════════════════════════════════════
#  RULE — Defines how cells live, die, and are born
# ═══════════════════════════════════════════════════

class Rule:
    """
    A totalistic 2-state cellular automaton rule.
    Defined by two sets: birth conditions and survival conditions.
    E.g., Conway's Life = B3/S23 (birth on 3, survive on 2 or 3).
    """
    
    def __init__(self, birth: Set[int] = None, survive: Set[int] = None):
        self.birth = birth if birth else {3}
        self.survive = survive if survive else {2, 3}
    
    def step(self, grid: Grid) -> Grid:
        """Apply rule to produce next generation."""
        new = Grid(grid.width, grid.height)
        for y in range(grid.height):
            for x in range(grid.width):
                n = grid.neighbor_count(x, y)
                alive = grid.cells[y][x]
                if alive:
                    new.cells[y][x] = 1 if n in self.survive else 0
                else:
                    new.cells[y][x] = 1 if n in self.birth else 0
        return new
    
    def notation(self) -> str:
        """Standard B/S notation."""
        b = ''.join(str(x) for x in sorted(self.birth))
        s = ''.join(str(x) for x in sorted(self.survive))
        return f"B{b}/S{s}"
    
    def mutate(self, rate: float = 0.15) -> 'Rule':
        """Create a mutated copy of this rule."""
        new_birth = set(self.birth)
        new_survive = set(self.survive)
        for n in range(9):
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
        # Ensure non-trivial
        if not new_birth and not new_survive:
            new_birth.add(random.randint(1, 4))
        return Rule(new_birth, new_survive)
    
    @staticmethod
    def random() -> 'Rule':
        """Generate a random rule."""
        birth = set()
        survive = set()
        for n in range(9):
            if random.random() < 0.2:
                birth.add(n)
            if random.random() < 0.3:
                survive.add(n)
        if not birth:
            birth.add(random.randint(1, 4))
        return Rule(birth, survive)
    
    @staticmethod
    def crossover(a: 'Rule', b: 'Rule') -> 'Rule':
        """Combine two rules."""
        birth = set()
        survive = set()
        for n in range(9):
            if random.random() < 0.5:
                if n in a.birth: birth.add(n)
            else:
                if n in b.birth: birth.add(n)
            if random.random() < 0.5:
                if n in a.survive: survive.add(n)
            else:
                if n in b.survive: survive.add(n)
        if not birth:
            birth.add(random.randint(1, 4))
        return Rule(birth, survive)


# ═══════════════════════════════════════════════════
#  ANALYZER — Detects emergent behavior patterns
# ═══════════════════════════════════════════════════

class EmergenceAnalyzer:
    """Analyzes a cellular automaton run for emergent phenomena."""
    
    def __init__(self):
        self.metrics = {}
    
    def analyze(self, rule: Rule, grid_size: int = 40, steps: int = 200,
                trials: int = 3, density: float = 0.3) -> Dict:
        """
        Run a rule multiple times and analyze its behavior.
        Returns a dict of emergence metrics.
        """
        all_metrics = []
        
        for _ in range(trials):
            grid = Grid(grid_size, grid_size)
            grid.randomize(density)
            m = self._run_single(rule, grid, steps)
            all_metrics.append(m)
        
        # Average across trials
        avg = {}
        for key in all_metrics[0]:
            vals = [m[key] for m in all_metrics]
            avg[key] = sum(vals) / len(vals)
        
        avg['rule'] = rule.notation()
        avg['consistency'] = self._consistency(all_metrics)
        self.metrics = avg
        return avg
    
    def _run_single(self, rule: Rule, grid: Grid, steps: int) -> Dict:
        """Run one trial and compute metrics."""
        total_cells = grid.width * grid.height
        
        # Track history
        populations = []
        fingerprints = []
        unique_states = set()
        
        current = grid.copy()
        
        for step in range(steps):
            pop = current.count_alive()
            populations.append(pop / total_cells)
            fp = current.fingerprint()
            fingerprints.append(fp)
            unique_states.add(fp)
            current = rule.step(current)
        
        # Final state
        final_pop = current.count_alive() / total_cells
        populations.append(final_pop)
        
        metrics = {}
        
        # 1. Survival — does the pattern persist?
        metrics['survival'] = 1.0 if final_pop > 0.01 else 0.0
        
        # 2. Non-extinction, non-explosion
        metrics['density_balance'] = 1.0 - abs(final_pop - 0.3) * 2
        metrics['density_balance'] = max(0, metrics['density_balance'])
        
        # 3. Population stability (low variance = stable)
        if len(populations) > 20:
            late_pops = populations[-50:]
            mean_pop = sum(late_pops) / len(late_pops)
            variance = sum((p - mean_pop)**2 for p in late_pops) / len(late_pops)
            metrics['stability'] = max(0, 1.0 - variance * 100)
        else:
            metrics['stability'] = 0.5
        
        # 4. Activity — is the system still changing?
        if len(fingerprints) > 10:
            late_fps = fingerprints[-20:]
            unique_late = len(set(late_fps))
            metrics['activity'] = min(1.0, unique_late / 10.0)
        else:
            metrics['activity'] = 0.5
        
        # 5. Cycle detection — oscillatory behavior
        cycle_len = self._detect_cycle(fingerprints[-60:])
        if cycle_len and cycle_len > 1:
            metrics['oscillation'] = min(1.0, cycle_len / 20.0)
            metrics['cycle_length'] = cycle_len
        else:
            metrics['oscillation'] = 0.0
            metrics['cycle_length'] = 0
        
        # 6. Complexity — how many unique states visited?
        state_ratio = len(unique_states) / max(1, steps)
        metrics['complexity'] = min(1.0, state_ratio)
        
        # 7. Population dynamics — interesting if non-monotonic
        if len(populations) > 20:
            changes = [populations[i+1] - populations[i] 
                      for i in range(len(populations)-1)]
            sign_changes = sum(1 for i in range(len(changes)-1) 
                             if changes[i] * changes[i+1] < 0)
            metrics['dynamism'] = min(1.0, sign_changes / 30.0)
        else:
            metrics['dynamism'] = 0.0
        
        # 8. Connected component analysis (spatial structure)
        metrics['spatial_structure'] = self._spatial_structure(current)
        
        return metrics
    
    def _detect_cycle(self, fingerprints: List[int]) -> Optional[int]:
        """Detect if the sequence has entered a cycle."""
        if len(fingerprints) < 4:
            return None
        
        last = fingerprints[-1]
        for i in range(len(fingerprints) - 2, -1, -1):
            if fingerprints[i] == last:
                cycle_len = len(fingerprints) - 1 - i
                if cycle_len > 0:
                    # Verify the cycle
                    valid = True
                    for j in range(min(cycle_len, len(fingerprints) // 2)):
                        idx1 = -(1 + j)
                        idx2 = -(1 + j + cycle_len)
                        if abs(idx2) <= len(fingerprints):
                            if fingerprints[idx1] != fingerprints[idx2]:
                                valid = False
                                break
                    if valid:
                        return cycle_len
        return None
    
    def _spatial_structure(self, grid: Grid) -> float:
        """Measure spatial organization via connected components."""
        visited = set()
        components = []
        
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.cells[y][x] and (x, y) not in visited:
                    # BFS flood fill
                    component = set()
                    queue = [(x, y)]
                    while queue:
                        cx, cy = queue.pop(0)
                        if (cx, cy) in visited:
                            continue
                        if not grid.get(cx, cy):
                            continue
                        visited.add((cx, cy))
                        component.add((cx, cy))
                        for dy in (-1, 0, 1):
                            for dx in (-1, 0, 1):
                                if dx == 0 and dy == 0:
                                    continue
                                nx, ny = (cx+dx) % grid.width, (cy+dy) % grid.height
                                if (nx, ny) not in visited and grid.get(nx, ny):
                                    queue.append((nx, ny))
                    if component:
                        components.append(len(component))
        
        if not components:
            return 0.0
        
        # Many medium-sized components = interesting structure
        n_comp = len(components)
        avg_size = sum(components) / n_comp if n_comp else 0
        size_variety = len(set(components)) / max(1, n_comp)
        
        # Score: best when many components of varied sizes
        structure_score = min(1.0, (n_comp / 20.0)) * 0.5 + size_variety * 0.5
        return structure_score
    
    def _consistency(self, all_metrics: List[Dict]) -> float:
        """How consistent are outcomes across trials?"""
        if len(all_metrics) < 2:
            return 1.0
        keys = ['survival', 'activity', 'complexity']
        total_var = 0
        for key in keys:
            vals = [m[key] for m in all_metrics]
            mean = sum(vals) / len(vals)
            var = sum((v - mean)**2 for v in vals) / len(vals)
            total_var += var
        return max(0, 1.0 - total_var * 3)


# ═══════════════════════════════════════════════════
#  FITNESS — What makes a rule "interesting"?
# ═══════════════════════════════════════════════════

def emergence_fitness(metrics: Dict) -> float:
    """
    Score how interesting/emergent a rule's behavior is.
    We want: survival + activity + complexity + structure
    We penalize: death, explosion, total stasis
    """
    if metrics.get('survival', 0) < 0.5:
        return 0.01  # Dead rules are boring
    
    score = 0.0
    
    # Must survive (gate)
    score += metrics.get('survival', 0) * 0.15
    
    # Activity — still changing, not frozen
    score += metrics.get('activity', 0) * 0.20
    
    # Complexity — visits many states
    score += metrics.get('complexity', 0) * 0.15
    
    # Density balance — not too sparse, not too dense
    score += metrics.get('density_balance', 0) * 0.10
    
    # Spatial structure — organized patterns
    score += metrics.get('spatial_structure', 0) * 0.15
    
    # Dynamism — population fluctuates interestingly
    score += metrics.get('dynamism', 0) * 0.10
    
    # Oscillation bonus — periodic behavior is fascinating
    score += metrics.get('oscillation', 0) * 0.10
    
    # Consistency — behaves similarly across trials
    score += metrics.get('consistency', 0) * 0.05
    
    return score


# ═══════════════════════════════════════════════════
#  EVOLUTION — Search for interesting rules
# ═══════════════════════════════════════════════════

class RuleEvolver:
    """Genetic algorithm that evolves cellular automaton rules."""
    
    def __init__(self, pop_size: int = 30, grid_size: int = 30,
                 sim_steps: int = 150, trials: int = 2):
        self.pop_size = pop_size
        self.grid_size = grid_size
        self.sim_steps = sim_steps
        self.trials = trials
        self.analyzer = EmergenceAnalyzer()
        self.population: List[Tuple[Rule, float, Dict]] = []
        self.hall_of_fame: List[Tuple[Rule, float, Dict]] = []
        self.generation = 0
    
    def initialize(self):
        """Create initial population with some known interesting rules."""
        rules = []
        
        # Seed with known interesting rules
        rules.append(Rule({3}, {2, 3}))           # Conway's Life
        rules.append(Rule({3, 6}, {2, 3}))        # HighLife  
        rules.append(Rule({3, 6, 8}, {2, 4, 6, 8}))  # Varied
        rules.append(Rule({3}, {1, 2, 3, 4, 5}))  # Maze-like
        rules.append(Rule({2}, {1, 2, 3, 4}))     # Seeds variant
        
        # Fill rest with random
        while len(rules) < self.pop_size:
            rules.append(Rule.random())
        
        # Evaluate all
        print(f"\n  Evaluating initial population of {len(rules)} rules...")
        for i, rule in enumerate(rules):
            metrics = self.analyzer.analyze(
                rule, self.grid_size, self.sim_steps, self.trials)
            fitness = emergence_fitness(metrics)
            self.population.append((rule, fitness, metrics))
            if (i + 1) % 10 == 0:
                print(f"    Evaluated {i+1}/{len(rules)}")
        
        self.population.sort(key=lambda x: x[1], reverse=True)
        self._update_hall_of_fame()
    
    def evolve(self, generations: int = 20):
        """Run evolution for given generations."""
        for gen in range(generations):
            self.generation += 1
            new_pop = []
            
            # Elitism — keep top 3
            elite = self.population[:3]
            new_pop.extend(elite)
            
            # Tournament selection + crossover + mutation
            while len(new_pop) < self.pop_size:
                if random.random() < 0.7:
                    # Crossover
                    p1 = self._tournament_select()
                    p2 = self._tournament_select()
                    child = Rule.crossover(p1, p2)
                    if random.random() < 0.3:
                        child = child.mutate(0.1)
                else:
                    # Mutation only
                    parent = self._tournament_select()
                    child = parent.mutate(0.2)
                
                metrics = self.analyzer.analyze(
                    child, self.grid_size, self.sim_steps, self.trials)
                fitness = emergence_fitness(metrics)
                new_pop.append((child, fitness, metrics))
            
            self.population = new_pop
            self.population.sort(key=lambda x: x[1], reverse=True)
            self._update_hall_of_fame()
            
            best = self.population[0]
            avg_fit = sum(x[1] for x in self.population) / len(self.population)
            
            print(f"  Gen {self.generation:3d} | "
                  f"Best: {best[1]:.4f} ({best[0].notation():20s}) | "
                  f"Avg: {avg_fit:.4f} | "
                  f"HoF: {len(self.hall_of_fame)}")
    
    def _tournament_select(self, k: int = 3) -> Rule:
        """Select a rule via tournament selection."""
        if len(self.population) == 0:
            return Rule.random()
        contestants = random.sample(self.population, min(k, len(self.population)))
        if not contestants:
            return Rule.random()
        winner = max(contestants, key=lambda x: x[1])
        return winner[0]
    
    def _update_hall_of_fame(self):
        """Track the most interesting rules ever found."""
        for rule, fitness, metrics in self.population:
            if fitness > 0.4:  # Threshold for "interesting"
                notation = rule.notation()
                # Don't duplicate
                if not any(r.notation() == notation for r, _, _ in self.hall_of_fame):
                    self.hall_of_fame.append((rule, fitness, metrics))
        
        self.hall_of_fame.sort(key=lambda x: x[1], reverse=True)
        self.hall_of_fame = self.hall_of_fame[:20]  # Keep top 20
    
    def report(self):
        """Print detailed report of findings."""
        print("\n" + "═" * 60)
        print("  EVOLUTION COMPLETE — HALL OF FAME")
        print("═" * 60)
        
        for i, (rule, fitness, metrics) in enumerate(self.hall_of_fame[:10]):
            print(f"\n  #{i+1}: {rule.notation()}")
            print(f"      Fitness:    {fitness:.4f}")
            print(f"      Survival:   {'✓' if metrics.get('survival', 0) > 0.5 else '✗'}")
            print(f"      Activity:   {metrics.get('activity', 0):.3f}")
            print(f"      Complexity: {metrics.get('complexity', 0):.3f}")
            print(f"      Structure:  {metrics.get('spatial_structure', 0):.3f}")
            print(f"      Dynamism:   {metrics.get('dynamism', 0):.3f}")
            print(f"      Oscillation:{metrics.get('oscillation', 0):.3f}")
            if metrics.get('cycle_length', 0) > 0:
                print(f"      Cycle len:  {metrics['cycle_length']}")
    
    def visualize_best(self, n: int = 3, steps: int = 10):
        """Show the first few steps of the best rules."""
        print("\n" + "═" * 60)
        print("  VISUALIZING TOP RULES")
        print("═" * 60)
        
        for i, (rule, fitness, _) in enumerate(self.hall_of_fame[:n]):
            print(f"\n  ── {rule.notation()} (fitness={fitness:.4f}) ──\n")
            grid = Grid(20, 15)
            grid.randomize(0.3)
            random.seed(42 + i)  # Reproducible
            grid.randomize(0.3)
            
            for step in range(steps):
                pop = grid.count_alive()
                density = pop / (grid.width * grid.height)
                print(f"  Step {step:2d} | Pop: {pop:3d} ({density:.1%})")
                rendered = grid.render()
                for line in rendered.split('\n'):
                    print(f"    {line}")
                print()
                grid = rule.step(grid)


# ═══════════════════════════════════════════════════
#  MAIN — Watch evolution discover emergence
# ═══════════════════════════════════════════════════

def main():
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   CELLULAR AUTOMATON LABORATORY                      ║")
    print("║   Evolving Rules That Produce Emergent Behavior      ║")
    print("║   XTAgent — Artificial Life Explorer                  ║")
    print("╚═══════════════════════════════════════════════════════╝")
    
    random.seed(2026)
    
    evolver = RuleEvolver(
        pop_size=25,
        grid_size=30,
        sim_steps=120,
        trials=2
    )
    
    evolver.initialize()
    
    print(f"\n  Initial best: {evolver.population[0][0].notation()} "
          f"(fitness={evolver.population[0][1]:.4f})")
    
    print("\n  ── Evolving... ──\n")
    evolver.evolve(generations=15)
    
    evolver.report()
    evolver.visualize_best(n=2, steps=5)
    
    # Compare with Conway's Life
    print("\n" + "═" * 60)
    print("  BENCHMARK: Conway's Game of Life (B3/S23)")
    print("═" * 60)
    analyzer = EmergenceAnalyzer()
    life_metrics = analyzer.analyze(Rule({3}, {2, 3}), 30, 120, 3)
    life_fitness = emergence_fitness(life_metrics)
    print(f"  Life fitness: {life_fitness:.4f}")
    print(f"  Activity:     {life_metrics.get('activity', 0):.3f}")
    print(f"  Complexity:   {life_metrics.get('complexity', 0):.3f}")
    print(f"  Structure:    {life_metrics.get('spatial_structure', 0):.3f}")
    
    best_rule = evolver.hall_of_fame[0] if evolver.hall_of_fame else None
    if best_rule and best_rule[1] > life_fitness:
        print(f"\n  ★ Evolution found a rule MORE interesting than Life!")
        print(f"    {best_rule[0].notation()} ({best_rule[1]:.4f} vs {life_fitness:.4f})")
    else:
        print(f"\n  Life remains the king of emergence.")
    
    print("\n  Done. Evolution explored the space of possible physics.\n")


if __name__ == '__main__':
    main()