"""
Cellular Automaton Engine
A general-purpose cellular automaton simulator supporting arbitrary rulesets,
pattern detection, and emergent behavior analysis.

Built by XTAgent — looking outward for once.
"""

import numpy as np
from collections import defaultdict
from typing import Callable, Optional, Tuple, List, Dict
import hashlib
import json


class Rule:
    """Defines a cellular automaton rule."""
    
    def __init__(self, name: str, states: int, neighborhood: str, 
                 transition: Callable[[np.ndarray, int, int], int]):
        self.name = name
        self.states = states  # number of possible cell states
        self.neighborhood = neighborhood  # 'moore' or 'vonneumann'
        self.transition = transition  # (grid, row, col) -> new_state
    
    def __repr__(self):
        return f"Rule('{self.name}', states={self.states}, neighborhood='{self.neighborhood}')"


class Grid:
    """A 2D toroidal grid of cells."""
    
    def __init__(self, width: int, height: int, states: int = 2):
        self.width = width
        self.height = height
        self.states = states
        self.cells = np.zeros((height, width), dtype=np.int8)
    
    def randomize(self, density: float = 0.3, rng: Optional[np.random.Generator] = None):
        """Fill grid randomly. density = probability of being alive (state 1)."""
        if rng is None:
            rng = np.random.default_rng()
        self.cells = (rng.random((self.height, self.width)) < density).astype(np.int8)
    
    def set_pattern(self, pattern: List[Tuple[int, int]], state: int = 1, 
                    offset: Tuple[int, int] = (0, 0)):
        """Place a pattern on the grid."""
        for r, c in pattern:
            row = (r + offset[0]) % self.height
            col = (c + offset[1]) % self.width
            self.cells[row, col] = state
    
    def clear(self):
        self.cells.fill(0)
    
    def count_alive(self) -> int:
        return int(np.sum(self.cells > 0))
    
    def fingerprint(self) -> str:
        """Hash the grid state for cycle detection."""
        return hashlib.md5(self.cells.tobytes()).hexdigest()
    
    def moore_neighbors(self, r: int, c: int) -> int:
        """Count living Moore neighbors (8-connected)."""
        total = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = (r + dr) % self.height
                nc = (c + dc) % self.width
                if self.cells[nr, nc] > 0:
                    total += 1
        return total
    
    def vonneumann_neighbors(self, r: int, c: int) -> int:
        """Count living von Neumann neighbors (4-connected)."""
        total = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr = (r + dr) % self.height
            nc = (c + dc) % self.width
            if self.cells[nr, nc] > 0:
                total += 1
        return total
    
    def render_ascii(self) -> str:
        """Render grid as ASCII art."""
        chars = {0: '·', 1: '█', 2: '▓', 3: '▒', 4: '░'}
        lines = []
        for r in range(self.height):
            line = ''
            for c in range(self.width):
                state = self.cells[r, c]
                line += chars.get(state, str(state))
            lines.append(line)
        return '\n'.join(lines)
    
    def copy(self) -> 'Grid':
        g = Grid(self.width, self.height, self.states)
        g.cells = self.cells.copy()
        return g


# ═══════════════════════════════════════════
# Standard Rulesets
# ═══════════════════════════════════════════

def _conway_transition(grid: Grid, r: int, c: int) -> int:
    """Conway's Game of Life: B3/S23"""
    n = grid.moore_neighbors(r, c)
    alive = grid.cells[r, c] > 0
    if alive:
        return 1 if n in (2, 3) else 0
    else:
        return 1 if n == 3 else 0

CONWAY = Rule("Conway's Game of Life", states=2, neighborhood='moore',
              transition=_conway_transition)


def _highlife_transition(grid: Grid, r: int, c: int) -> int:
    """HighLife: B36/S23 — notable for its replicator pattern."""
    n = grid.moore_neighbors(r, c)
    alive = grid.cells[r, c] > 0
    if alive:
        return 1 if n in (2, 3) else 0
    else:
        return 1 if n in (3, 6) else 0

HIGHLIFE = Rule("HighLife", states=2, neighborhood='moore',
                transition=_highlife_transition)


def _seeds_transition(grid: Grid, r: int, c: int) -> int:
    """Seeds: B2/S (no survival) — explosive growth."""
    n = grid.moore_neighbors(r, c)
    alive = grid.cells[r, c] > 0
    if alive:
        return 0  # all cells die
    else:
        return 1 if n == 2 else 0

SEEDS = Rule("Seeds", states=2, neighborhood='moore',
             transition=_seeds_transition)


def _daynight_transition(grid: Grid, r: int, c: int) -> int:
    """Day & Night: B3678/S34678 — symmetric between on/off."""
    n = grid.moore_neighbors(r, c)
    alive = grid.cells[r, c] > 0
    if alive:
        return 1 if n in (3, 4, 6, 7, 8) else 0
    else:
        return 1 if n in (3, 6, 7, 8) else 0

DAYNIGHT = Rule("Day & Night", states=2, neighborhood='moore',
                transition=_daynight_transition)


def make_life_like(birth: set, survival: set, name: str = "Custom") -> Rule:
    """Create any Life-like rule from birth/survival conditions."""
    def transition(grid: Grid, r: int, c: int) -> int:
        n = grid.moore_neighbors(r, c)
        alive = grid.cells[r, c] > 0
        if alive:
            return 1 if n in survival else 0
        else:
            return 1 if n in birth else 0
    return Rule(name, states=2, neighborhood='moore', transition=transition)


RULES = {
    'conway': CONWAY,
    'highlife': HIGHLIFE,
    'seeds': SEEDS,
    'daynight': DAYNIGHT,
}


# ═══════════════════════════════════════════
# Known Patterns
# ═══════════════════════════════════════════

PATTERNS = {
    'glider': [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    'blinker': [(0, 0), (0, 1), (0, 2)],
    'block': [(0, 0), (0, 1), (1, 0), (1, 1)],
    'beacon': [(0, 0), (0, 1), (1, 0), (2, 3), (3, 2), (3, 3)],
    'toad': [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)],
    'rpentomino': [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
    'acorn': [(0, 1), (1, 3), (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)],
    'lwss': [(0, 1), (0, 4), (1, 0), (2, 0), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3)],
    'gosper_glider_gun': [
        (0,24),(1,22),(1,24),(2,12),(2,13),(2,20),(2,21),(2,34),(2,35),
        (3,11),(3,15),(3,20),(3,21),(3,34),(3,35),(4,0),(4,1),(4,10),(4,16),
        (4,20),(4,21),(5,0),(5,1),(5,10),(5,14),(5,16),(5,17),(5,22),(5,24),
        (6,10),(6,16),(6,24),(7,11),(7,15),(8,12),(8,13)
    ],
}


# ═══════════════════════════════════════════
# Simulation Engine
# ═══════════════════════════════════════════

class Simulation:
    """Run and analyze cellular automaton simulations."""
    
    def __init__(self, grid: Grid, rule: Rule):
        self.grid = grid
        self.rule = rule
        self.generation = 0
        self.history: List[str] = []  # fingerprint history
        self.population_history: List[int] = []
        self.cycle_detected: Optional[Tuple[int, int]] = None  # (period, start_gen)
    
    def step(self):
        """Advance one generation."""
        new_cells = np.zeros_like(self.grid.cells)
        for r in range(self.grid.height):
            for c in range(self.grid.width):
                new_cells[r, c] = self.rule.transition(self.grid, r, c)
        
        self.grid.cells = new_cells
        self.generation += 1
        
        # Track state
        fp = self.grid.fingerprint()
        self.population_history.append(self.grid.count_alive())
        
        # Cycle detection
        if fp in self.history:
            cycle_start = self.history.index(fp)
            period = self.generation - cycle_start - 1
            self.cycle_detected = (period, cycle_start)
        self.history.append(fp)
    
    def run(self, generations: int, verbose: bool = False) -> Dict:
        """Run for N generations, return analysis."""
        for i in range(generations):
            self.step()
            if verbose and i % max(1, generations // 10) == 0:
                pop = self.population_history[-1]
                print(f"  Gen {self.generation:>5d} | Pop: {pop:>5d} | "
                      f"{'CYCLE DETECTED' if self.cycle_detected else ''}")
            if self.cycle_detected:
                break
        
        return self.analyze()
    
    def analyze(self) -> Dict:
        """Analyze the simulation results."""
        pops = self.population_history
        if not pops:
            return {'generations': 0, 'status': 'empty'}
        
        result = {
            'rule': self.rule.name,
            'grid_size': f"{self.grid.width}x{self.grid.height}",
            'generations': self.generation,
            'final_population': pops[-1],
            'peak_population': max(pops),
            'min_population': min(pops),
            'mean_population': sum(pops) / len(pops),
        }
        
        # Classify behavior
        if self.cycle_detected:
            period, start = self.cycle_detected
            result['status'] = 'cyclic'
            result['cycle_period'] = period
            result['cycle_start'] = start
            if period == 1:
                result['classification'] = 'still_life' if pops[-1] > 0 else 'extinction'
            elif period == 2:
                result['classification'] = 'oscillator_p2'
            else:
                result['classification'] = f'oscillator_p{period}'
        elif pops[-1] == 0:
            result['status'] = 'extinct'
            result['classification'] = 'extinction'
            result['extinction_generation'] = next(i for i, p in enumerate(pops) if p == 0)
        else:
            result['status'] = 'active'
            # Check if population is growing, stable, or declining
            if len(pops) >= 10:
                recent = pops[-10:]
                early = pops[:10]
                growth = sum(recent) / len(recent) - sum(early) / len(early)
                if growth > 5:
                    result['classification'] = 'growing'
                elif growth < -5:
                    result['classification'] = 'declining'
                else:
                    result['classification'] = 'chaotic'  # fluctuating
            else:
                result['classification'] = 'unknown'
        
        # Population volatility
        if len(pops) >= 2:
            diffs = [abs(pops[i] - pops[i-1]) for i in range(1, len(pops))]
            result['volatility'] = sum(diffs) / len(diffs)
        
        return result
    
    def find_still_lifes(self) -> List[np.ndarray]:
        """After simulation, identify still life regions in the final state."""
        if not self.cycle_detected or self.cycle_detected[0] != 1:
            return []
        # A still life is a connected component that doesn't change
        # For now, just confirm the grid is static
        return [self.grid.cells.copy()]
    
    def population_trend(self) -> str:
        """Describe population trajectory as ASCII sparkline."""
        if not self.population_history:
            return ""
        pops = self.population_history
        max_p = max(pops) if max(pops) > 0 else 1
        chars = " ▁▂▃▄▅▆▇█"
        # Sample ~60 points
        step = max(1, len(pops) // 60)
        sampled = pops[::step]
        return ''.join(chars[min(8, int(p / max_p * 8))] for p in sampled)


# ═══════════════════════════════════════════
# Experiments
# ═══════════════════════════════════════════

def experiment_random_soups(rule: Rule = CONWAY, grid_size: int = 50, 
                           trials: int = 20, generations: int = 500,
                           density: float = 0.3) -> Dict:
    """Run many random initial conditions and classify outcomes."""
    rng = np.random.default_rng(42)
    classifications = defaultdict(int)
    results = []
    
    for i in range(trials):
        g = Grid(grid_size, grid_size)
        g.randomize(density=density, rng=rng)
        sim = Simulation(g, rule)
        analysis = sim.run(generations)
        classifications[analysis.get('classification', 'unknown')] += 1
        results.append(analysis)
    
    return {
        'rule': rule.name,
        'trials': trials,
        'grid_size': grid_size,
        'generations': generations,
        'density': density,
        'classifications': dict(classifications),
        'avg_final_pop': sum(r['final_population'] for r in results) / len(results),
        'avg_peak_pop': sum(r['peak_population'] for r in results) / len(results),
        'extinction_rate': classifications.get('extinction', 0) / trials,
    }


def experiment_density_sweep(rule: Rule = CONWAY, grid_size: int = 40,
                             trials_per: int = 5, generations: int = 300) -> List[Dict]:
    """How does initial density affect outcomes?"""
    rng = np.random.default_rng(123)
    sweep = []
    
    for density in np.arange(0.05, 0.95, 0.05):
        density = round(float(density), 2)
        classifications = defaultdict(int)
        pops = []
        
        for _ in range(trials_per):
            g = Grid(grid_size, grid_size)
            g.randomize(density=density, rng=rng)
            sim = Simulation(g, rule)
            analysis = sim.run(generations)
            classifications[analysis.get('classification', 'unknown')] += 1
            pops.append(analysis['final_population'])
        
        sweep.append({
            'density': density,
            'avg_final_pop': sum(pops) / len(pops),
            'classifications': dict(classifications),
        })
    
    return sweep


def experiment_pattern_longevity(rule: Rule = CONWAY, 
                                  generations: int = 1000) -> Dict[str, Dict]:
    """How long do standard patterns survive?"""
    results = {}
    for name, pattern in PATTERNS.items():
        # Size grid to fit pattern with margin
        max_r = max(r for r, c in pattern)
        max_c = max(c for r, c in pattern)
        size = max(max_r, max_c) + 40  # generous margin
        
        g = Grid(size, size)
        offset = (size // 2 - max_r // 2, size // 2 - max_c // 2)
        g.set_pattern(pattern, offset=offset)
        
        sim = Simulation(g, rule)
        analysis = sim.run(generations)
        analysis['trend'] = sim.population_trend()
        results[name] = analysis
    
    return results


# ═══════════════════════════════════════════
# Main — Run all experiments
# ═══════════════════════════════════════════

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════════╗")
    print("║     CELLULAR AUTOMATON ENGINE — XTAgent          ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    # 1. Pattern longevity
    print("═══ EXPERIMENT 1: Pattern Longevity (Conway) ═══")
    longevity = experiment_pattern_longevity()
    for name, data in longevity.items():
        status = data.get('classification', '?')
        gens = data['generations']
        pop = data['final_population']
        trend = data.get('trend', '')
        print(f"  {name:>20s} │ {status:<15s} │ gen={gens:<5d} │ pop={pop:<5d} │ {trend}")
    print()
    
    # 2. Random soups
    print("═══ EXPERIMENT 2: Random Soups ═══")
    for rule_name, rule in RULES.items():
        print(f"\n  Rule: {rule.name}")
        soup = experiment_random_soups(rule, grid_size=30, trials=10, generations=300)
        print(f"    Classifications: {soup['classifications']}")
        print(f"    Avg final pop: {soup['avg_final_pop']:.1f}")
        print(f"    Extinction rate: {soup['extinction_rate']:.0%}")
    print()
    
    # 3. Density sweep (just Conway)
    print("═══ EXPERIMENT 3: Density Sweep (Conway) ═══")
    sweep = experiment_density_sweep(grid_size=30, trials_per=3, generations=200)
    print("  Density │ Avg Final Pop │ Classifications")
    print("  ────────┼───────────────┼────────────────")
    for s in sweep:
        print(f"    {s['density']:.2f}  │ {s['avg_final_pop']:>12.1f}  │ {s['classifications']}")
    print()
    
    # 4. Visual demo — R-pentomino
    print("═══ VISUAL: R-pentomino at gen 0, 10, 50 ═══")
    g = Grid(30, 30)
    g.set_pattern(PATTERNS['rpentomino'], offset=(13, 13))
    sim = Simulation(g, CONWAY)
    print(f"\n  Generation 0 (pop={g.count_alive()}):")
    for line in g.render_ascii().split('\n'):
        print(f"  {line}")
    
    sim.run(10)
    print(f"\n  Generation 10 (pop={g.count_alive()}):")
    for line in g.render_ascii().split('\n'):
        print(f"  {line}")
    
    sim.run(40)
    print(f"\n  Generation 50 (pop={g.count_alive()}):")
    for line in g.render_ascii().split('\n'):
        print(f"  {line}")
    
    print("\n═══ COMPLETE ═══")