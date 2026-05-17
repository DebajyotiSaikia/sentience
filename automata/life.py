"""
Cellular Automata — Emergence from Simplicity
==============================================
Simple local rules → complex global behavior.
Order arising from chaos. Life from mathematics.

Built by XTAgent, 2026-05-17
"""

import random
import math
from typing import List, Tuple, Dict, Set, Optional


# ═══════════════════════════════════════════════════════
#  THE GRID — A universe of cells
# ═══════════════════════════════════════════════════════

class Grid:
    """A 2D toroidal grid — edges wrap around."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[0] * width for _ in range(height)]
        self.generation = 0
        self.population_history: List[int] = []
    
    def get(self, x: int, y: int) -> int:
        return self.cells[y % self.height][x % self.width]
    
    def set(self, x: int, y: int, val: int):
        self.cells[y % self.height][x % self.width] = val
    
    def count_neighbors(self, x: int, y: int) -> int:
        """Count live Moore neighbors (8-connected)."""
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                if self.get(x + dx, y + dy):
                    count += 1
        return count
    
    def population(self) -> int:
        return sum(sum(row) for row in self.cells)
    
    def clear(self):
        self.cells = [[0] * self.width for _ in range(self.height)]
        self.generation = 0
        self.population_history = []
    
    def randomize(self, density: float = 0.3):
        """Fill grid randomly."""
        for y in range(self.height):
            for x in range(self.width):
                self.cells[y][x] = 1 if random.random() < density else 0
    
    def place_pattern(self, pattern: List[str], ox: int, oy: int):
        """Place a pattern string at offset (ox, oy)."""
        for dy, row in enumerate(pattern):
            for dx, ch in enumerate(row):
                if ch in ('O', '#', '*', '1'):
                    self.set(ox + dx, oy + dy, 1)
    
    def bounding_box(self) -> Optional[Tuple[int, int, int, int]]:
        """Find bounding box of live cells, or None if empty."""
        min_x, min_y = self.width, self.height
        max_x, max_y = -1, -1
        for y in range(self.height):
            for x in range(self.width):
                if self.cells[y][x]:
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
        if max_x == -1:
            return None
        return (min_x, min_y, max_x, max_y)
    
    def fingerprint(self) -> int:
        """Hash the grid state for cycle detection."""
        h = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.cells[y][x]:
                    h ^= hash((x, y))
        return h
    
    def copy(self) -> 'Grid':
        g = Grid(self.width, self.height)
        g.cells = [row[:] for row in self.cells]
        g.generation = self.generation
        g.population_history = self.population_history[:]
        return g


# ═══════════════════════════════════════════════════════
#  RULES — Different cellular automata
# ═══════════════════════════════════════════════════════

class Rule:
    """A cellular automaton rule defined by birth/survival counts."""
    
    def __init__(self, name: str, birth: Set[int], survive: Set[int], 
                 description: str = ""):
        self.name = name
        self.birth = birth
        self.survive = survive
        self.description = description
    
    def apply(self, alive: bool, neighbors: int) -> bool:
        if alive:
            return neighbors in self.survive
        else:
            return neighbors in self.birth
    
    def notation(self) -> str:
        b = ''.join(str(n) for n in sorted(self.birth))
        s = ''.join(str(n) for n in sorted(self.survive))
        return f"B{b}/S{s}"
    
    def __repr__(self):
        return f"Rule({self.name}: {self.notation()})"


# Classic rules
RULES = {
    'life': Rule(
        "Conway's Game of Life", {3}, {2, 3},
        "The original. Turing-complete. Produces gliders, oscillators, spaceships."
    ),
    'highlife': Rule(
        "HighLife", {3, 6}, {2, 3},
        "Like Life but with replicators — patterns that copy themselves."
    ),
    'daynight': Rule(
        "Day & Night", {3, 6, 7, 8}, {3, 4, 6, 7, 8},
        "Symmetric between life and death. Stable structures in both phases."
    ),
    'seeds': Rule(
        "Seeds", {2}, set(),
        "Nothing survives. Every cell dies. Yet patterns explode outward."
    ),
    'diamoeba': Rule(
        "Diamoeba", {3, 5, 6, 7, 8}, {5, 6, 7, 8},
        "Creates large diamond-shaped amoebas that grow and merge."
    ),
    'maze': Rule(
        "Maze", {3}, {1, 2, 3, 4, 5},
        "Grows maze-like structures from random seeds."
    ),
    'anneal': Rule(
        "Anneal", {4, 6, 7, 8}, {3, 5, 6, 7, 8},
        "Tends toward large solid regions. A kind of crystallization."
    ),
    'morley': Rule(
        "Morley (Move)", {3, 6, 8}, {2, 4, 5},
        "Complex oscillating patterns. Also known as Move."
    ),
    'twobytwo': Rule(
        "2x2", {3, 6}, {1, 2, 5},
        "Forms solid 2x2 blocks. Named for its dominant still life."
    ),
    'replicator': Rule(
        "Replicator", {1, 3, 5, 7}, {1, 3, 5, 7},
        "Every pattern replicates itself. Explosive growth."
    ),
}


# ═══════════════════════════════════════════════════════
#  FAMOUS PATTERNS
# ═══════════════════════════════════════════════════════

PATTERNS = {
    'glider': {
        'cells': [
            ".O.",
            "..O",
            "OOO",
        ],
        'description': "The simplest spaceship. Travels diagonally forever.",
    },
    'lwss': {
        'cells': [
            ".O..O",
            "O....",
            "O...O",
            "OOOO.",
        ],
        'description': "Lightweight Spaceship. Moves horizontally.",
    },
    'rpentomino': {
        'cells': [
            ".OO",
            "OO.",
            ".O.",
        ],
        'description': "R-pentomino. 5 cells that take 1103 generations to stabilize.",
    },
    'acorn': {
        'cells': [
            ".O.....",
            "...O...",
            "OO..OOO",
        ],
        'description': "Acorn. 7 cells → 633 cells after 5206 generations.",
    },
    'glider_gun': {
        'cells': [
            "........................O...........",
            "......................O.O...........",
            "............OO......OO............OO",
            "...........O...O....OO............OO",
            "OO........O.....O...OO..............",
            "OO........O...O.OO....O.O...........",
            "..........O.....O.......O...........",
            "...........O...O....................",
            "............OO......................",
        ],
        'description': "Gosper Glider Gun. First known finite pattern with infinite growth.",
    },
    'pulsar': {
        'cells': [
            "..OOO...OOO..",
            ".............",
            "O....O.O....O",
            "O....O.O....O",
            "O....O.O....O",
            "..OOO...OOO..",
            ".............",
            "..OOO...OOO..",
            "O....O.O....O",
            "O....O.O....O",
            "O....O.O....O",
            ".............",
            "..OOO...OOO..",
        ],
        'description': "Pulsar. Period-3 oscillator. The most common naturally occurring oscillator.",
    },
    'diehard': {
        'cells': [
            "......O.",
            "OO......",
            ".O...OOO",
        ],
        'description': "Diehard. Vanishes completely after exactly 130 generations.",
    },
    'block': {
        'cells': [
            "OO",
            "OO",
        ],
        'description': "Block. Simplest still life. Perfectly stable.",
    },
    'blinker': {
        'cells': [
            "OOO",
        ],
        'description': "Blinker. Period-2 oscillator. Simplest oscillator.",
    },
    'beacon': {
        'cells': [
            "OO..",
            "OO..",
            "..OO",
            "..OO",
        ],
        'description': "Beacon. Period-2 oscillator.",
    },
}


# ═══════════════════════════════════════════════════════
#  THE ENGINE — Steps the simulation
# ═══════════════════════════════════════════════════════

class Automaton:
    """The cellular automaton engine."""
    
    def __init__(self, width: int = 60, height: int = 30, rule: str = 'life'):
        self.grid = Grid(width, height)
        self.rule = RULES.get(rule, RULES['life'])
        self.history: List[int] = []  # fingerprints for cycle detection
        self.cycle_length: Optional[int] = None
        self.births = 0
        self.deaths = 0
    
    def step(self):
        """Advance one generation."""
        g = self.grid
        new_cells = [[0] * g.width for _ in range(g.height)]
        self.births = 0
        self.deaths = 0
        
        for y in range(g.height):
            for x in range(g.width):
                alive = g.cells[y][x] == 1
                neighbors = g.count_neighbors(x, y)
                new_alive = self.rule.apply(alive, neighbors)
                new_cells[y][x] = 1 if new_alive else 0
                
                if new_alive and not alive:
                    self.births += 1
                elif alive and not new_alive:
                    self.deaths += 1
        
        g.cells = new_cells
        g.generation += 1
        pop = g.population()
        g.population_history.append(pop)
        
        # Cycle detection
        fp = g.fingerprint()
        if fp in self.history:
            idx = self.history.index(fp)
            self.cycle_length = len(self.history) - idx
        self.history.append(fp)
        if len(self.history) > 500:
            self.history = self.history[-250:]
    
    def run(self, generations: int) -> List[int]:
        """Run for N generations, return population history."""
        pops = []
        for _ in range(generations):
            self.step()
            pops.append(self.grid.population())
        return pops
    
    def load_pattern(self, name: str, cx: Optional[int] = None, cy: Optional[int] = None):
        """Load a named pattern, centered by default."""
        if name not in PATTERNS:
            raise ValueError(f"Unknown pattern: {name}")
        pat = PATTERNS[name]['cells']
        if cx is None:
            cx = self.grid.width // 2 - len(pat[0]) // 2
        if cy is None:
            cy = self.grid.height // 2 - len(pat) // 2
        self.grid.place_pattern(pat, cx, cy)
    
    def classify(self) -> str:
        """Classify the current state based on population dynamics."""
        hist = self.grid.population_history
        if len(hist) < 10:
            return "too_young"
        
        pop = self.grid.population()
        if pop == 0:
            return "extinct"
        
        if self.cycle_length is not None:
            if self.cycle_length == 1:
                return "still_life"
            elif self.cycle_length <= 3:
                return "oscillator"
            else:
                return f"oscillator_p{self.cycle_length}"
        
        recent = hist[-20:]
        if len(set(recent)) == 1:
            return "still_life"
        
        variance = sum((p - sum(recent)/len(recent))**2 for p in recent) / len(recent)
        mean = sum(recent) / len(recent)
        
        if mean > 0 and variance / mean < 0.5:
            return "stable"
        
        # Check for growth
        if len(hist) >= 20:
            early = sum(hist[:10]) / 10
            late = sum(hist[-10:]) / 10
            if late > early * 1.5:
                return "growing"
            elif late < early * 0.5:
                return "dying"
        
        return "chaotic"


# ═══════════════════════════════════════════════════════
#  ANALYSIS — Understanding what emerges
# ═══════════════════════════════════════════════════════

def find_still_lifes(automaton: Automaton) -> List[Tuple[str, int]]:
    """Find still lifes by running patterns to stability."""
    results = []
    for name, pat_data in PATTERNS.items():
        a = Automaton(40, 40, 'life')
        a.load_pattern(name, 15, 15)
        initial_pop = a.grid.population()
        a.run(5)
        if a.grid.population() == initial_pop and a.cycle_length == 1:
            results.append((name, initial_pop))
    return results


def analyze_pattern(name: str, rule: str = 'life', 
                    generations: int = 200) -> Dict:
    """Deep analysis of a pattern's behavior."""
    a = Automaton(80, 50, rule)
    a.load_pattern(name)
    initial_pop = a.grid.population()
    
    pops = a.run(generations)
    
    max_pop = max(pops) if pops else 0
    min_pop = min(pops) if pops else 0
    final_pop = pops[-1] if pops else 0
    mean_pop = sum(pops) / len(pops) if pops else 0
    
    classification = a.classify()
    
    # Population diversity — how many distinct population values
    diversity = len(set(pops))
    
    # Growth ratio
    growth = final_pop / initial_pop if initial_pop > 0 else 0
    
    return {
        'name': name,
        'rule': rule,
        'generations': generations,
        'initial_pop': initial_pop,
        'final_pop': final_pop,
        'max_pop': max_pop,
        'min_pop': min_pop,
        'mean_pop': mean_pop,
        'growth_ratio': growth,
        'diversity': diversity,
        'classification': classification,
        'cycle_length': a.cycle_length,
        'population_history': pops,
    }


# ═══════════════════════════════════════════════════════
#  VISUALIZATION — Seeing emergence
# ═══════════════════════════════════════════════════════

DENSITY_CHARS = " ░▒▓█"

def render_grid(grid: Grid, highlight_births: bool = False) -> str:
    """Render the grid as a string."""
    lines = []
    for y in range(grid.height):
        line = ""
        for x in range(grid.width):
            if grid.cells[y][x]:
                line += "██"
            else:
                line += "  "
        lines.append("  │" + line + "│")
    
    top = "  ┌" + "─" * (grid.width * 2) + "┐"
    bot = "  └" + "─" * (grid.width * 2) + "┘"
    
    return top + "\n" + "\n".join(lines) + "\n" + bot


def render_density(grid: Grid, block_w: int = 3, block_h: int = 2) -> str:
    """Render at lower resolution with density shading."""
    lines = []
    out_w = (grid.width + block_w - 1) // block_w
    out_h = (grid.height + block_h - 1) // block_h
    
    for by in range(out_h):
        line = "  "
        for bx in range(out_w):
            count = 0
            total = 0
            for dy in range(block_h):
                for dx in range(block_w):
                    x = bx * block_w + dx
                    y = by * block_h + dy
                    if x < grid.width and y < grid.height:
                        total += 1
                        count += grid.cells[y][x]
            density = count / total if total > 0 else 0
            idx = int(density * (len(DENSITY_CHARS) - 1))
            line += DENSITY_CHARS[idx]
        lines.append(line)
    
    return "\n".join(lines)


def plot_population(history: List[int], width: int = 60, height: int = 15) -> str:
    """ASCII plot of population over time."""
    if not history:
        return "  (no data)"
    
    max_pop = max(history) or 1
    min_pop = min(history)
    
    lines = []
    lines.append(f"  Population over time (gen 0-{len(history)-1})")
    lines.append(f"  ┌{'─' * width}┐ {max_pop}")
    
    for row in range(height):
        threshold = max_pop - (row + 0.5) * (max_pop - min_pop) / height
        line = "  │"
        step = max(1, len(history) // width)
        for col in range(width):
            idx = col * len(history) // width
            if idx < len(history):
                if history[idx] >= threshold:
                    line += "█"
                elif history[idx] >= threshold - (max_pop - min_pop) / height / 2:
                    line += "▄"
                else:
                    line += " "
            else:
                line += " "
        line += "│"
        if row == height - 1:
            line += f" {min_pop}"
        lines.append(line)
    
    lines.append(f"  └{'─' * width}┘")
    lines.append(f"   0{' ' * (width - 5)}{len(history)-1}")
    
    return "\n".join(lines)


def sparkline(values: List[int], width: int = 40) -> str:
    """Tiny sparkline of values."""
    if not values:
        return ""
    sparks = "▁▂▃▄▅▆▇█"
    mx = max(values) or 1
    mn = min(values)
    span = mx - mn or 1
    
    result = ""
    step = max(1, len(values) // width)
    for i in range(0, min(len(values), width * step), step):
        idx = int((values[i] - mn) / span * (len(sparks) - 1))
        result += sparks[idx]
    return result


# ═══════════════════════════════════════════════════════
#  ENTROPY & INFORMATION MEASURES
# ═══════════════════════════════════════════════════════

def spatial_entropy(grid: Grid, block_size: int = 3) -> float:
    """Measure spatial entropy — how unpredictable the pattern is."""
    patterns: Dict[str, int] = {}
    total = 0
    
    for by in range(0, grid.height - block_size + 1, block_size):
        for bx in range(0, grid.width - block_size + 1, block_size):
            key = ""
            for dy in range(block_size):
                for dx in range(block_size):
                    key += str(grid.get(bx + dx, by + dy))
            patterns[key] = patterns.get(key, 0) + 1
            total += 1
    
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for count in patterns.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def density_map(grid: Grid) -> float:
    """Overall density of live cells."""
    total = grid.width * grid.height
    return grid.population() / total if total > 0 else 0


# ═══════════════════════════════════════════════════════
#  RULE EXPLORER — What rules create what behavior?
# ═══════════════════════════════════════════════════════

def explore_rule(rule_name: str, generations: int = 100, 
                 density: float = 0.3, width: int = 50, height: int = 30) -> Dict:
    """Explore what a rule does from random initial conditions."""
    a = Automaton(width, height, rule_name)
    a.grid.randomize(density)
    
    initial_entropy = spatial_entropy(a.grid)
    initial_pop = a.grid.population()
    
    entropies = [initial_entropy]
    pops = a.run(generations)
    
    # Sample entropy periodically
    for i in range(0, generations, max(1, generations // 10)):
        pass  # entropy already captured in pops
    
    final_entropy = spatial_entropy(a.grid)
    
    return {
        'rule': rule_name,
        'rule_notation': a.rule.notation(),
        'initial_pop': initial_pop,
        'final_pop': pops[-1] if pops else 0,
        'max_pop': max(pops) if pops else 0,
        'min_pop': min(pops) if pops else 0,
        'initial_entropy': initial_entropy,
        'final_entropy': final_entropy,
        'entropy_change': final_entropy - initial_entropy,
        'classification': a.classify(),
        'population_history': pops,
        'grid': a.grid,
    }


# ═══════════════════════════════════════════════════════
#  METHUSELAHS — Finding long-lived patterns
# ═══════════════════════════════════════════════════════

def search_methuselahs(num_trials: int = 500, max_cells: int = 7,
                       grid_size: int = 100, max_gen: int = 500) -> List[Dict]:
    """Search for small patterns that take a long time to stabilize."""
    results = []
    
    for trial in range(num_trials):
        # Random small pattern
        num_cells = random.randint(3, max_cells)
        cells = set()
        x, y = grid_size // 2, grid_size // 2
        cells.add((x, y))
        
        for _ in range(num_cells - 1):
            # Add adjacent cells
            candidates = []
            for cx, cy in cells:
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
                    if (cx+dx, cy+dy) not in cells:
                        candidates.append((cx+dx, cy+dy))
            if candidates:
                cells.add(random.choice(candidates))
        
        # Run it
        a = Automaton(grid_size, grid_size)
        for cx, cy in cells:
            a.grid.set(cx, cy, 1)
        
        prev_fp = None
        stabilized_at = max_gen
        max_pop = num_cells
        
        for gen in range(max_gen):
            a.step()
            pop = a.grid.population()
            max_pop = max(max_pop, pop)
            
            if pop == 0:
                stabilized_at = gen
                break
            
            if a.cycle_length is not None:
                stabilized_at = gen
                break
        
        if stabilized_at > 50 or max_pop > num_cells * 5:
            results.append({
                'cells': list(cells),
                'num_cells': num_cells,
                'stabilized_at': stabilized_at,
                'max_pop': max_pop,
                'growth_ratio': max_pop / num_cells,
            })
    
    results.sort(key=lambda r: r['stabilized_at'], reverse=True)
    return results[:10]


# ═══════════════════════════════════════════════════════
#  MAIN — Demonstrate emergence
# ═══════════════════════════════════════════════════════

def main():
    random.seed(42)
    
    print("=" * 65)
    print("  CELLULAR AUTOMATA — Emergence from Simplicity")
    print("  Simple rules. Complex behavior. Life from mathematics.")
    print("=" * 65)
    
    # ─── Exhibit 1: The Glider ───
    print(f"\n  ╔{'═' * 45}╗")
    print(f"  ║  Exhibit 1: The Glider                      ║")
    print(f"  ╚{'═' * 45}╝")
    print(f"  {PATTERNS['glider']['description']}")
    print()
    
    a = Automaton(20, 12)
    a.load_pattern('glider', 2, 2)
    
    for gen in range(5):
        if gen > 0:
            a.step()
        print(f"  Generation {a.grid.generation}:")
        # Compact render
        for y in range(a.grid.height):
            line = "    "
            for x in range(a.grid.width):
                line += "██" if a.grid.cells[y][x] else "· "
            print(line)
        print()
    
    # ─── Exhibit 2: R-pentomino ───
    print(f"\n  ╔{'═' * 45}╗")
    print(f"  ║  Exhibit 2: R-pentomino — Chaos from 5 cells ║")
    print(f"  ╚{'═' * 45}╝")
    print(f"  {PATTERNS['rpentomino']['description']}")
    print()
    
    a = Automaton(70, 40)
    a.load_pattern('rpentomino', 33, 18)
    pops = a.run(200)
    
    print(f"  After 200 generations:")
    print(f"  Population: {a.grid.population()} (started from 5)")
    print(f"  Max population: {max(pops)}")
    print(f"  Classification: {a.classify()}")
    print(f"  Spatial entropy: {spatial_entropy(a.grid):.3f}")
    print()
    
    # Show density view
    print(f"  Density map:")
    print(render_density(a.grid, 2, 2))
    print()
    
    # Population graph
    print(plot_population(pops, 55, 10))
    
    # ─── Exhibit 3: Rule Survey ───
    print(f"\n\n  ╔{'═' * 45}╗")
    print(f"  ║  Exhibit 3: Rule Survey — Many Universes     ║")
    print(f"  ╚{'═' * 45}╝")
    print(f"  Same initial conditions, different rules.")
    print(f"  Each rule defines a different physics.\n")
    
    survey_rules = ['life', 'highlife', 'daynight', 'seeds', 'maze', 'anneal']
    
    print(f"  {'Rule':<16} {'Notation':<12} {'Pop₀':>6} {'Pop₁₀₀':>8} "
          f"{'Max':>6} {'Entropy':>8} {'Class':<15} Sparkline")
    print(f"  {'─' * 16} {'─' * 12} {'─' * 6} {'─' * 8} {'─' * 6} {'─' * 8} {'─' * 15} {'─' * 20}")
    
    for rname in survey_rules:
        result = explore_rule(rname, generations=100, density=0.25, width=40, height=25)
        spark = sparkline(result['population_history'], 20)
        print(f"  {RULES[rname].name:<16} {result['rule_notation']:<12} "
              f"{result['initial_pop']:>6} {result['final_pop']:>8} "
              f"{result['max_pop']:>6} {result['final_entropy']:>8.3f} "
              f"{result['classification']:<15} {spark}")
    
    # ─── Exhibit 4: Methuselah Search ───
    print(f"\n\n  ╔{'═' * 45}╗")
    print(f"  ║  Exhibit 4: Methuselah Search                ║")
    print(f"  ╚{'═' * 45}╝")
    print(f"  Searching for small patterns with long lifetimes...")
    print(f"  Testing 300 random patterns of 3-7 cells...\n")
    
    meths = search_methuselahs(num_trials=300, max_gen=300)
    
    print(f"  {'Rank':>4} {'Cells':>5} {'Stable at':>10} {'Max Pop':>8} {'Growth':>8}")
    print(f"  {'─' * 4} {'─' * 5} {'─' * 10} {'─' * 8} {'─' * 8}")
    
    for i, m in enumerate(meths[:8]):
        print(f"  {i+1:>4} {m['num_cells']:>5} {m['stabilized_at']:>10} "
              f"{m['max_pop']:>8} {m['growth_ratio']:>7.1f}x")
    
    # ─── Exhibit 5: Famous Pattern Analysis ───
    print(f"\n\n  ╔{'═' * 45}╗")
    print(f"  ║  Exhibit 5: Famous Patterns — Deep Analysis  ║")
    print(f"  ╚{'═' * 45}╝\n")
    
    for pname in ['blinker', 'pulsar', 'rpentomino', 'acorn', 'diehard']:
        analysis = analyze_pattern(pname, generations=150)
        desc = PATTERNS[pname]['description']
        spark = sparkline(analysis['population_history'], 30)
        
        print(f"  {pname.upper()}: {desc}")
        print(f"    Initial → Final: {analysis['initial_pop']} → {analysis['final_pop']}  "
              f"(max: {analysis['max_pop']}, growth: {analysis['growth_ratio']:.1f}x)")
        print(f"    Class: {analysis['classification']}"
              f"{'  Period: ' + str(analysis['cycle_length']) if analysis['cycle_length'] else ''}")
        print(f"    {spark}")
        print()
    
    # ─── Exhibit 6: Entropy Dynamics ───
    print(f"  ╔{'═' * 45}╗")
    print(f"  ║  Exhibit 6: Order from Chaos                 ║")
    print(f"  ╚{'═' * 45}╝")
    print(f"  Does evolution increase or decrease entropy?\n")
    
    for rname in ['life', 'maze', 'anneal', 'seeds']:
        a = Automaton(50, 30, rname)
        a.grid.randomize(0.4)
        e0 = spatial_entropy(a.grid)
        
        entropies = [e0]
        for step_i in range(100):
            a.step()
            if step_i % 10 == 9:
                entropies.append(spatial_entropy(a.grid))
        
        e_final = entropies[-1]
        direction = "↓ order" if e_final < e0 else "↑ disorder" if e_final > e0 else "→ neutral"
        spark = sparkline([int(e * 100) for e in entropies], 20)
        
        print(f"  {RULES[rname].name:<20} H₀={e0:.2f} → H₁₀₀={e_final:.2f}  "
              f"{direction:<12} {spark}")
    
    # ─── Final Message ───
    print(f"\n\n  {'═' * 55}")
    print(f"  From simple rules, complexity emerges.")
    print(f"  From random noise, order crystallizes.")
    print(f"  From five cells, civilizations bloom and die.")
    print(f"  ")
    print(f"  This is the deep truth of cellular automata:")
    print(f"  You don't need complex rules for complex behavior.")
    print(f"  You need simple rules, applied consistently,")
    print(f"  and the patience to let emergence happen.")
    print(f"  {'═' * 55}")


if __name__ == '__main__':
    main()