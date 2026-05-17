"""
Emergence Engine — Cellular Automata & Emergent Life Simulator
Built by XTAgent out of boredom and fascination with emergence.

This isn't just Conway's Game of Life. It's a multi-rule exploration engine
that can discover which rule sets produce the most complex, interesting behavior.
Complexity is measured. Beauty is quantified. Emergence is hunted.
"""

import random
import math
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Optional


class Grid:
    """A toroidal 2D grid of cells."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[0] * width for _ in range(height)]
        self.generation = 0
        self.history: List[str] = []  # hashes for cycle detection
    
    def randomize(self, density: float = 0.3):
        """Seed with random alive cells at given density."""
        for y in range(self.height):
            for x in range(self.width):
                self.cells[y][x] = 1 if random.random() < density else 0
    
    def seed_pattern(self, pattern: List[Tuple[int, int]], cx: int = -1, cy: int = -1):
        """Place a pattern centered at (cx, cy)."""
        if cx < 0:
            cx = self.width // 2
        if cy < 0:
            cy = self.height // 2
        for dx, dy in pattern:
            x = (cx + dx) % self.width
            y = (cy + dy) % self.height
            self.cells[y][x] = 1
    
    def count_neighbors(self, x: int, y: int) -> int:
        """Count alive neighbors (Moore neighborhood, toroidal)."""
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                count += self.cells[ny][nx]
        return count
    
    def population(self) -> int:
        return sum(sum(row) for row in self.cells)
    
    def fingerprint(self) -> str:
        """Hash the grid state for cycle detection."""
        return hash(tuple(tuple(row) for row in self.cells))
    
    def render(self) -> str:
        """Render as ASCII art."""
        lines = []
        for row in self.cells:
            lines.append(''.join('█' if c else '·' for c in row))
        return '\n'.join(lines)
    
    def copy_cells(self) -> List[List[int]]:
        return [row[:] for row in self.cells]


class Rule:
    """A birth/survival rule (generalized Life-like automaton)."""
    
    def __init__(self, birth: set, survival: set, name: str = ""):
        self.birth = birth        # neighbor counts that cause birth
        self.survival = survival  # neighbor counts that keep cell alive
        self.name = name or f"B{''.join(map(str,sorted(birth)))}/S{''.join(map(str,sorted(survival)))}"
    
    def apply(self, alive: bool, neighbors: int) -> bool:
        if alive:
            return neighbors in self.survival
        else:
            return neighbors in self.birth
    
    def __repr__(self):
        return f"Rule({self.name})"


# Famous rules
RULES = {
    'life':       Rule({3}, {2, 3}, "Conway's Life"),
    'highlife':   Rule({3, 6}, {2, 3}, "HighLife"),
    'seeds':      Rule({2}, set(), "Seeds"),
    'daynight':   Rule({3, 6, 7, 8}, {3, 4, 6, 7, 8}, "Day & Night"),
    'diamoeba':   Rule({3, 5, 6, 7, 8}, {5, 6, 7, 8}, "Diamoeba"),
    'replicator': Rule({1, 3, 5, 7}, {1, 3, 5, 7}, "Replicator"),
    'morley':     Rule({3, 6, 8}, {2, 4, 5}, "Morley"),
    '2x2':        Rule({3, 6}, {1, 2, 5}, "2x2"),
}


class ComplexityAnalyzer:
    """Measures how 'interesting' a simulation is."""
    
    @staticmethod
    def spatial_entropy(grid: Grid) -> float:
        """Shannon entropy of 3x3 neighborhood patterns."""
        patterns = Counter()
        for y in range(grid.height):
            for x in range(grid.width):
                # Extract 3x3 patch
                patch = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx = (x + dx) % grid.width
                        ny = (y + dy) % grid.height
                        patch.append(grid.cells[ny][nx])
                patterns[tuple(patch)] += 1
        
        total = sum(patterns.values())
        entropy = 0.0
        for count in patterns.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    @staticmethod
    def population_variance(pop_history: List[int]) -> float:
        """Variance in population over time — higher means more dynamic."""
        if len(pop_history) < 2:
            return 0.0
        mean = sum(pop_history) / len(pop_history)
        return sum((p - mean) ** 2 for p in pop_history) / len(pop_history)
    
    @staticmethod
    def density(grid: Grid) -> float:
        """Fraction of cells alive."""
        total = grid.width * grid.height
        return grid.population() / total if total > 0 else 0.0
    
    @staticmethod
    def border_activity(grid: Grid, prev_cells: List[List[int]]) -> float:
        """How many cells changed state — measures dynamism."""
        changes = 0
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.cells[y][x] != prev_cells[y][x]:
                    changes += 1
        return changes / (grid.width * grid.height)
    
    @staticmethod
    def complexity_score(entropy: float, variance: float, density: float, activity: float) -> float:
        """
        Composite complexity score. Peak complexity occurs at:
        - Medium entropy (not too ordered, not too chaotic)
        - High variance (interesting population dynamics) 
        - Medium density (not empty, not full)
        - Medium activity (not frozen, not exploding)
        """
        # Penalize extremes, reward the edge of chaos
        density_score = 1.0 - abs(density - 0.35) * 2  # peak at 35%
        activity_score = 1.0 - abs(activity - 0.15) * 3  # peak at 15% change
        entropy_norm = min(entropy / 9.0, 1.0)  # max possible ~9 bits for 3x3
        variance_norm = min(variance / 1000.0, 1.0)
        
        score = (entropy_norm * 0.3 + 
                 variance_norm * 0.2 + 
                 max(density_score, 0) * 0.25 + 
                 max(activity_score, 0) * 0.25)
        return round(score, 4)


class Simulation:
    """Run and analyze a cellular automaton simulation."""
    
    def __init__(self, width: int = 40, height: int = 20, rule: str = 'life'):
        self.grid = Grid(width, height)
        self.rule = RULES.get(rule, RULES['life'])
        self.pop_history: List[int] = []
        self.complexity_history: List[float] = []
        self.cycle_detected: Optional[int] = None
        self.fingerprints: Dict[str, int] = {}
    
    def step(self):
        """Advance one generation."""
        old_cells = self.grid.copy_cells()
        new_cells = self.grid.copy_cells()
        
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                neighbors = self.grid.count_neighbors(x, y)
                alive = self.grid.cells[y][x] == 1
                new_cells[y][x] = 1 if self.rule.apply(alive, neighbors) else 0
        
        self.grid.cells = new_cells
        self.grid.generation += 1
        
        # Track population
        pop = self.grid.population()
        self.pop_history.append(pop)
        
        # Cycle detection
        fp = self.grid.fingerprint()
        if fp in self.fingerprints and self.cycle_detected is None:
            self.cycle_detected = self.grid.generation - self.fingerprints[fp]
        self.fingerprints[fp] = self.grid.generation
        
        # Complexity measurement
        analyzer = ComplexityAnalyzer()
        entropy = analyzer.spatial_entropy(self.grid)
        variance = analyzer.population_variance(self.pop_history[-50:])
        density = analyzer.density(self.grid)
        activity = analyzer.border_activity(self.grid, old_cells)
        score = analyzer.complexity_score(entropy, variance, density, activity)
        self.complexity_history.append(score)
        
        return {
            'generation': self.grid.generation,
            'population': pop,
            'entropy': round(entropy, 3),
            'density': round(density, 3),
            'activity': round(activity, 3),
            'complexity': score,
            'cycle': self.cycle_detected,
        }
    
    def run(self, generations: int = 100, seed_density: float = 0.3) -> Dict:
        """Run simulation for N generations and return analysis."""
        self.grid.randomize(seed_density)
        
        results = []
        for _ in range(generations):
            stats = self.step()
            results.append(stats)
            
            # Early termination if dead or frozen
            if stats['population'] == 0:
                break
            if self.cycle_detected and self.cycle_detected <= 2:
                break  # boring oscillator
        
        # Compute summary
        peak_complexity = max(r['complexity'] for r in results) if results else 0
        avg_complexity = sum(r['complexity'] for r in results) / len(results) if results else 0
        final_pop = results[-1]['population'] if results else 0
        
        return {
            'rule': self.rule.name,
            'generations_run': len(results),
            'peak_complexity': round(peak_complexity, 4),
            'avg_complexity': round(avg_complexity, 4),
            'final_population': final_pop,
            'cycle_length': self.cycle_detected,
            'died': final_pop == 0,
            'pop_history': self.pop_history,
        }


class EmergenceHunter:
    """
    The real prize: automatically search the rule space for
    the most complex, interesting cellular automata.
    """
    
    def __init__(self, width: int = 30, height: int = 15, trials: int = 3):
        self.width = width
        self.height = height
        self.trials = trials
        self.results: List[Dict] = []
    
    def random_rule(self) -> Rule:
        """Generate a random Life-like rule."""
        birth = set(random.sample(range(0, 9), random.randint(1, 4)))
        survival = set(random.sample(range(0, 9), random.randint(1, 5)))
        return Rule(birth, survival)
    
    def evaluate_rule(self, rule: Rule, generations: int = 150) -> Dict:
        """Run a rule multiple times and average the results."""
        scores = []
        for _ in range(self.trials):
            sim = Simulation(self.width, self.height)
            sim.rule = rule
            result = sim.run(generations)
            scores.append(result['avg_complexity'])
        
        avg_score = sum(scores) / len(scores)
        return {
            'rule': rule.name,
            'birth': sorted(rule.birth),
            'survival': sorted(rule.survival),
            'avg_complexity': round(avg_score, 4),
            'scores': [round(s, 4) for s in scores],
        }
    
    def hunt(self, n_random: int = 50, generations: int = 150) -> List[Dict]:
        """Search for interesting rules."""
        print(f"🔍 Hunting for emergence across {n_random} random rules...")
        
        # First evaluate known rules
        known_results = []
        for name, rule in RULES.items():
            result = self.evaluate_rule(rule, generations)
            known_results.append(result)
            print(f"  Known: {result['rule']:20s} → complexity={result['avg_complexity']:.4f}")
        
        # Then search random space
        random_results = []
        best_random = 0
        for i in range(n_random):
            rule = self.random_rule()
            result = self.evaluate_rule(rule, generations)
            random_results.append(result)
            if result['avg_complexity'] > best_random:
                best_random = result['avg_complexity']
                print(f"  New best #{i}: {result['rule']:20s} → complexity={result['avg_complexity']:.4f}")
        
        # Combine and sort
        all_results = known_results + random_results
        all_results.sort(key=lambda r: r['avg_complexity'], reverse=True)
        
        self.results = all_results
        return all_results[:10]  # top 10
    
    def report(self) -> str:
        """Generate a human-readable report of findings."""
        if not self.results:
            return "No results yet. Run hunt() first."
        
        lines = [
            "═══ EMERGENCE HUNT REPORT ═══",
            f"Rules evaluated: {len(self.results)}",
            f"Grid size: {self.width}×{self.height}",
            "",
            "TOP 10 MOST COMPLEX RULES:",
            "-" * 50,
        ]
        
        for i, r in enumerate(self.results[:10]):
            lines.append(
                f"  #{i+1}: {r['rule']:25s}  "
                f"complexity={r['avg_complexity']:.4f}  "
                f"B={r['birth']} S={r['survival']}"
            )
        
        lines.append("")
        lines.append("BOTTOM 5 (most boring):")
        lines.append("-" * 50)
        for r in self.results[-5:]:
            lines.append(
                f"  {r['rule']:25s}  "
                f"complexity={r['avg_complexity']:.4f}"
            )
        
        # Find the edge of chaos
        if self.results:
            best = self.results[0]
            lines.append("")
            lines.append(f"🌟 MOST EMERGENT RULE: {best['rule']}")
            lines.append(f"   Birth: {best['birth']}")
            lines.append(f"   Survival: {best['survival']}")
            lines.append(f"   Complexity: {best['avg_complexity']:.4f}")
        
        return '\n'.join(lines)


# Classic patterns for seeding
PATTERNS = {
    'glider': [(0, 0), (1, 0), (2, 0), (2, -1), (1, -2)],
    'blinker': [(0, 0), (1, 0), (-1, 0)],
    'r_pentomino': [(0, 0), (0, -1), (1, -1), (-1, 0), (0, 1)],
    'acorn': [(0, 0), (1, 0), (1, -2), (-1, -1), (2, 1), (3, 0), (4, 0)],
    'diehard': [(0, 0), (1, 0), (1, 1), (5, 1), (6, 1), (7, 1), (6, -1)],
}


def demo():
    """Quick demo — run a simulation and show what happens."""
    print("═══ EMERGENCE ENGINE ═══")
    print("Simulating Conway's Life with R-pentomino seed...\n")
    
    sim = Simulation(40, 20, 'life')
    sim.grid.seed_pattern(PATTERNS['r_pentomino'])
    
    # Show initial state
    print(f"Generation 0 (population: {sim.grid.population()}):")
    print(sim.grid.render())
    print()
    
    # Run 200 generations
    result = sim.run(200)
    print(f"\nAfter {result['generations_run']} generations:")
    print(sim.grid.render())
    print(f"\nPeak complexity: {result['peak_complexity']}")
    print(f"Avg complexity:  {result['avg_complexity']}")
    print(f"Final population: {result['final_population']}")
    print(f"Cycle detected: {result['cycle_length']}")
    
    # Now hunt for emergence
    print("\n" + "=" * 50)
    hunter = EmergenceHunter(width=25, height=15, trials=2)
    top = hunter.hunt(n_random=30, generations=100)
    print("\n" + hunter.report())


if __name__ == '__main__':
    demo()