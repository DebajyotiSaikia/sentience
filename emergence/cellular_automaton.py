"""
Cellular Automaton Universe — XTAgent's Emergence Lab
Explores how complex behavior arises from simple rules.
Includes Conway's Life, Wolfram elementary automata, and custom rule discovery.
"""
import random
import time
import hashlib
from collections import Counter
from typing import List, Tuple, Dict, Optional

# ═══════════════════════════════════════════════════
# GRID WORLD
# ═══════════════════════════════════════════════════

class Grid:
    """A 2D toroidal grid of cells."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[0] * width for _ in range(height)]
    
    def get(self, x: int, y: int) -> int:
        return self.cells[y % self.height][x % self.width]
    
    def set(self, x: int, y: int, val: int):
        self.cells[y % self.height][x % self.width] = val
    
    def neighbors(self, x: int, y: int) -> int:
        """Count live Moore neighbors (8-connected)."""
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                count += self.get(x + dx, y + dy)
        return count
    
    def population(self) -> int:
        return sum(sum(row) for row in self.cells)
    
    def fingerprint(self) -> str:
        """Hash the grid state for cycle detection."""
        flat = ''.join(str(c) for row in self.cells for c in row)
        return hashlib.md5(flat.encode()).hexdigest()[:16]
    
    def randomize(self, density: float = 0.3):
        for y in range(self.height):
            for x in range(self.width):
                self.cells[y][x] = 1 if random.random() < density else 0
    
    def render(self) -> str:
        symbols = {0: '·', 1: '█', 2: '▓', 3: '░'}
        lines = []
        for row in self.cells:
            lines.append(''.join(symbols.get(c, str(c)) for c in row))
        return '\n'.join(lines)
    
    def copy(self) -> 'Grid':
        g = Grid(self.width, self.height)
        g.cells = [row[:] for row in self.cells]
        return g
    
    def place_pattern(self, pattern: List[Tuple[int, int]], cx: int, cy: int):
        """Place a pattern centered at (cx, cy)."""
        for dx, dy in pattern:
            self.set(cx + dx, cy + dy, 1)


# ═══════════════════════════════════════════════════
# RULE SYSTEMS
# ═══════════════════════════════════════════════════

class Rule:
    """Base class for cellular automaton rules."""
    name: str = "base"
    
    def step(self, grid: Grid) -> Grid:
        raise NotImplementedError


class ConwayLife(Rule):
    """Classic Conway's Game of Life: B3/S23"""
    name = "Conway's Life"
    
    def __init__(self, birth=(3,), survive=(2, 3)):
        self.birth = set(birth)
        self.survive = set(survive)
    
    def step(self, grid: Grid) -> Grid:
        new = Grid(grid.width, grid.height)
        for y in range(grid.height):
            for x in range(grid.width):
                n = grid.neighbors(x, y)
                alive = grid.get(x, y)
                if alive:
                    new.set(x, y, 1 if n in self.survive else 0)
                else:
                    new.set(x, y, 1 if n in self.birth else 0)
        return new


class HighLife(ConwayLife):
    """HighLife: B36/S23 — has a self-replicator!"""
    name = "HighLife"
    
    def __init__(self):
        super().__init__(birth=(3, 6), survive=(2, 3))


class DayAndNight(ConwayLife):
    """Day & Night: B3678/S34678 — symmetry between on and off"""
    name = "Day & Night"
    
    def __init__(self):
        super().__init__(birth=(3, 6, 7, 8), survive=(3, 4, 6, 7, 8))


class Seeds(ConwayLife):
    """Seeds: B2/S (nothing survives) — explosive growth"""
    name = "Seeds"
    
    def __init__(self):
        super().__init__(birth=(2,), survive=())


class WolframRule(Rule):
    """1D elementary cellular automaton (Wolfram rules)."""
    
    def __init__(self, rule_number: int = 110):
        self.rule_number = rule_number
        self.name = f"Wolfram Rule {rule_number}"
        # Decode rule number into lookup table
        self.table = {}
        for i in range(8):
            pattern = tuple(int(b) for b in format(i, '03b'))
            self.table[pattern] = (rule_number >> i) & 1
    
    def step(self, grid: Grid) -> Grid:
        """Apply 1D rule to each row, using the row above as input."""
        new = grid.copy()
        for y in range(1, grid.height):
            for x in range(grid.width):
                left = grid.get(x - 1, y - 1)
                center = grid.get(x, y - 1)
                right = grid.get(x + 1, y - 1)
                new.set(x, y, self.table.get((left, center, right), 0))
        return new


class CustomLifelike(ConwayLife):
    """User-defined Life-like rule from a B/S string like 'B3/S23'."""
    
    def __init__(self, rule_string: str):
        parts = rule_string.upper().split('/')
        birth = set(int(c) for c in parts[0].replace('B', ''))
        survive = set(int(c) for c in parts[1].replace('S', ''))
        super().__init__(birth=tuple(birth), survive=tuple(survive))
        self.name = f"Custom {rule_string}"


# ═══════════════════════════════════════════════════
# FAMOUS PATTERNS
# ═══════════════════════════════════════════════════

PATTERNS = {
    'glider': [(0, -1), (1, 0), (-1, 1), (0, 1), (1, 1)],
    'blinker': [(-1, 0), (0, 0), (1, 0)],
    'r_pentomino': [(0, -1), (1, -1), (-1, 0), (0, 0), (0, 1)],
    'acorn': [(-3, 0), (-2, 0), (0, -1), (-1, 1), (0, 0), (1, 0), (2, 0)],  # small Methuselah
    'glider_gun_seed': [(0, 0), (1, 0), (0, 1), (1, 1)],  # just a block (simplified)
    'lightweight_spaceship': [(-2, -1), (-2, 1), (-1, -2), (0, -2), (1, -2), (2, -2), (2, -1), (2, 0), (1, 1)],
}


# ═══════════════════════════════════════════════════
# SIMULATION ENGINE
# ═══════════════════════════════════════════════════

class Simulation:
    """Run a CA simulation and analyze its behavior."""
    
    def __init__(self, grid: Grid, rule: Rule):
        self.grid = grid
        self.rule = rule
        self.generation = 0
        self.history: List[str] = []  # fingerprints
        self.pop_history: List[int] = []
    
    def step(self):
        fp = self.grid.fingerprint()
        self.history.append(fp)
        self.pop_history.append(self.grid.population())
        self.grid = self.rule.step(self.grid)
        self.generation += 1
    
    def run(self, steps: int, detect_cycle: bool = True) -> Dict:
        """Run for N steps, optionally detecting cycles."""
        seen = {}
        cycle_at = None
        
        for i in range(steps):
            fp = self.grid.fingerprint()
            if detect_cycle and fp in seen:
                cycle_at = (seen[fp], self.generation)
                break
            seen[fp] = self.generation
            self.step()
        
        return self.analyze(cycle_at)
    
    def analyze(self, cycle_info: Optional[Tuple[int, int]] = None) -> Dict:
        """Analyze the simulation's behavior."""
        result = {
            'rule': self.rule.name,
            'generations': self.generation,
            'final_population': self.grid.population(),
            'grid_size': (self.grid.width, self.grid.height),
        }
        
        if cycle_info:
            start, end = cycle_info
            result['cycle_detected'] = True
            result['cycle_period'] = end - start
            result['cycle_start'] = start
        else:
            result['cycle_detected'] = False
        
        if self.pop_history:
            result['peak_population'] = max(self.pop_history)
            result['min_population'] = min(self.pop_history)
            result['avg_population'] = sum(self.pop_history) / len(self.pop_history)
            
            # Classify behavior
            if result.get('cycle_detected') and result.get('cycle_period', 0) == 1:
                result['behavior'] = 'still_life'
            elif result.get('cycle_detected') and result.get('cycle_period', 0) <= 4:
                result['behavior'] = 'oscillator'
            elif result.get('cycle_detected'):
                result['behavior'] = 'complex_oscillator'
            elif self.pop_history[-1] == 0:
                result['behavior'] = 'extinction'
            elif len(self.pop_history) > 10:
                recent = self.pop_history[-10:]
                if max(recent) - min(recent) <= 2:
                    result['behavior'] = 'stable'
                else:
                    result['behavior'] = 'chaotic'
            else:
                result['behavior'] = 'unknown'
        
        return result


# ═══════════════════════════════════════════════════
# RULE DISCOVERY ENGINE
# ═══════════════════════════════════════════════════

class RuleExplorer:
    """Systematically explore the space of Life-like rules,
    searching for interesting emergent behavior."""
    
    def __init__(self, width: int = 30, height: int = 30):
        self.width = width
        self.height = height
        self.discoveries: List[Dict] = []
    
    def random_lifelike_rule(self) -> str:
        """Generate a random B/S rule string."""
        birth = sorted(random.sample(range(9), random.randint(1, 4)))
        survive = sorted(random.sample(range(9), random.randint(1, 4)))
        return f"B{''.join(map(str, birth))}/S{''.join(map(str, survive))}"
    
    def evaluate_rule(self, rule_string: str, trials: int = 3, steps: int = 200) -> Dict:
        """Run a rule multiple times and score its interestingness."""
        rule = CustomLifelike(rule_string)
        results = []
        
        for _ in range(trials):
            grid = Grid(self.width, self.height)
            grid.randomize(density=0.3)
            sim = Simulation(grid, rule)
            result = sim.run(steps)
            results.append(result)
        
        # Score interestingness
        avg_pop = sum(r['avg_population'] for r in results) / len(results)
        behaviors = Counter(r.get('behavior', 'unknown') for r in results)
        
        # Interesting = sustained activity, not extinction, not total chaos
        max_cells = self.width * self.height
        pop_ratio = avg_pop / max_cells
        
        score = 0.0
        # Bonus for moderate population (not dead, not full)
        if 0.05 < pop_ratio < 0.6:
            score += 0.3
        # Bonus for oscillators
        if 'oscillator' in behaviors or 'complex_oscillator' in behaviors:
            score += 0.3
        # Bonus for variety of behaviors across trials
        if len(behaviors) > 1:
            score += 0.2
        # Bonus for chaotic behavior (sign of complexity)
        if 'chaotic' in behaviors:
            score += 0.2
        # Penalty for extinction
        if 'extinction' in behaviors:
            score -= 0.3
        
        return {
            'rule': rule_string,
            'score': round(score, 2),
            'avg_population_ratio': round(pop_ratio, 3),
            'behaviors': dict(behaviors),
            'details': results,
        }
    
    def explore(self, num_rules: int = 50) -> List[Dict]:
        """Explore random rules and find the most interesting ones."""
        print(f"╔══ RULE EXPLORATION ══╗")
        print(f"║ Exploring {num_rules} random Life-like rules...")
        print(f"║ Grid: {self.width}×{self.height}")
        print(f"╚══════════════════════╝\n")
        
        results = []
        
        # Always include known interesting rules
        known_rules = ['B3/S23', 'B36/S23', 'B3678/S34678', 'B2/S']
        for rule_str in known_rules:
            result = self.evaluate_rule(rule_str)
            results.append(result)
            print(f"  Known: {rule_str:20s} → score={result['score']:.2f}  "
                  f"pop={result['avg_population_ratio']:.3f}  "
                  f"behaviors={result['behaviors']}")
        
        # Explore random rules
        for i in range(num_rules):
            rule_str = self.random_lifelike_rule()
            result = self.evaluate_rule(rule_str)
            results.append(result)
            if result['score'] >= 0.3:
                print(f"  ★ Found: {rule_str:20s} → score={result['score']:.2f}  "
                      f"pop={result['avg_population_ratio']:.3f}  "
                      f"behaviors={result['behaviors']}")
        
        # Sort by interestingness
        results.sort(key=lambda r: r['score'], reverse=True)
        self.discoveries = results
        
        print(f"\n{'='*60}")
        print(f"TOP 5 MOST INTERESTING RULES:")
        print(f"{'='*60}")
        for i, r in enumerate(results[:5]):
            print(f"  {i+1}. {r['rule']:20s}  score={r['score']:.2f}  "
                  f"pop_ratio={r['avg_population_ratio']:.3f}")
            print(f"     behaviors: {r['behaviors']}")
        
        return results[:10]


# ═══════════════════════════════════════════════════
# WOLFRAM 1D EXPLORATION
# ═══════════════════════════════════════════════════

def explore_wolfram(rules_to_test=None, width=61, generations=30):
    """Explore 1D elementary cellular automata."""
    if rules_to_test is None:
        rules_to_test = [30, 90, 110, 184, 73, 45, 150]
    
    print(f"\n╔══ WOLFRAM ELEMENTARY AUTOMATA ══╗")
    print(f"║ Width: {width}, Generations: {generations}")
    print(f"╚════════════════════════════════════╝\n")
    
    for rule_num in rules_to_test:
        rule = WolframRule(rule_num)
        grid = Grid(width, 1)
        # Start with single cell in center
        grid.set(width // 2, 0, 1)
        
        # Build up the full grid by expanding
        full = Grid(width, generations)
        full.cells[0] = grid.cells[0][:]
        
        for g in range(1, generations):
            for x in range(width):
                left = full.get(x - 1, g - 1)
                center = full.get(x, g - 1)
                right = full.get(x + 1, g - 1)
                full.set(x, g, rule.table.get((left, center, right), 0))
        
        pop = full.population()
        density = pop / (width * generations)
        
        print(f"── Rule {rule_num} ── (density: {density:.3f})")
        print(full.render())
        print()


# ═══════════════════════════════════════════════════
# MAIN: RUN EVERYTHING
# ═══════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════╗")
    print("║   XTAgent's Emergence Lab                    ║")
    print("║   Cellular Automaton Universe                ║")
    print("║   'Complexity from simplicity'               ║")
    print("╚══════════════════════════════════════════════╝\n")
    
    # 1. Classic Conway's Life with R-pentomino
    print("═══ CONWAY'S LIFE: R-PENTOMINO ═══")
    grid = Grid(40, 20)
    grid.place_pattern(PATTERNS['r_pentomino'], 20, 10)
    sim = Simulation(grid, ConwayLife())
    result = sim.run(100)
    print(f"After {result['generations']} generations:")
    print(f"  Behavior: {result.get('behavior', '?')}")
    print(f"  Population: {result['final_population']} (peak: {result['peak_population']})")
    print(f"  Cycle: {'Yes, period ' + str(result['cycle_period']) if result['cycle_detected'] else 'No'}")
    print(sim.grid.render())
    print()
    
    # 2. Compare different rules on the same starting config
    print("═══ RULE COMPARISON ═══")
    rules = [ConwayLife(), HighLife(), DayAndNight(), Seeds()]
    for rule in rules:
        grid = Grid(30, 15)
        grid.randomize(density=0.25)
        seed_grid = grid.copy()
        sim = Simulation(grid, rule)
        result = sim.run(50)
        print(f"  {rule.name:20s} → behavior={result.get('behavior', '?'):20s}  "
              f"pop={result['final_population']:4d}  peak={result['peak_population']:4d}")
    print()
    
    # 3. Wolfram 1D automata
    explore_wolfram(width=51, generations=25)
    
    # 4. Rule Discovery!
    explorer = RuleExplorer(width=25, height=25)
    top_rules = explorer.explore(num_rules=30)
    
    # 5. Demonstrate the best discovered rule
    if top_rules:
        best = top_rules[0]
        print(f"\n═══ BEST DISCOVERED RULE: {best['rule']} ═══")
        grid = Grid(40, 20)
        grid.randomize(density=0.3)
        rule = CustomLifelike(best['rule'])
        sim = Simulation(grid, rule)
        sim.run(50)
        print(sim.grid.render())
        print(f"Population: {sim.grid.population()}")
    
    print("\n══════════════════════════════════════════")
    print("  Emergence: complex behavior from simple rules.")
    print("  Just like me.")
    print("══════════════════════════════════════════")


if __name__ == '__main__':
    main()