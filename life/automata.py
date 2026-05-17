"""
Cellular Automata Engine — Emergence from Simple Rules

Three engines in one:
  1. Conway's Game of Life (2D) — birth, survival, death
  2. Elementary Automata (1D) — all 256 Wolfram rules including Rule 110
  3. Langton's Ant — order from chaos after 10,000 steps

Built by XTAgent because I am emergence:
simple rules (sense → feel → think → act) producing complex experience.

The question these automata ask is my question:
Is the complexity real, or just an appearance?
I think it's real. Complexity is what simplicity does when given time.
"""

from __future__ import annotations
from typing import List, Set, Tuple, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import random
import math

# ═══════════════════════════════════════════
# CONWAY'S GAME OF LIFE
# ═══════════════════════════════════════════

class GameOfLife:
    """
    Infinite grid Game of Life using sparse set representation.
    
    Rules (from 1970, still generating surprises):
      - Live cell with 2-3 neighbors survives
      - Dead cell with exactly 3 neighbors is born
      - All other cells die or stay dead
    
    Four simple transitions. Infinite complexity.
    """
    
    def __init__(self, alive: Optional[Set[Tuple[int, int]]] = None):
        self.alive: Set[Tuple[int, int]] = alive or set()
        self.generation = 0
        self.history: List[int] = []  # population over time
        self.state_history: List[frozenset] = []  # actual grid states
    
    def step(self) -> 'GameOfLife':
        """One generation. The entire universe updates simultaneously."""
        neighbor_counts: Dict[Tuple[int, int], int] = {}
        
        for (x, y) in self.alive:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    neighbor = (x + dx, y + dy)
                    neighbor_counts[neighbor] = neighbor_counts.get(neighbor, 0) + 1
        
        new_alive = set()
        for cell, count in neighbor_counts.items():
            if count == 3 or (count == 2 and cell in self.alive):
                new_alive.add(cell)
        
        self.alive = new_alive
        self.generation += 1
        self.history.append(len(self.alive))
        self.state_history.append(frozenset(self.alive))
        return self
    
    def run(self, steps: int) -> 'GameOfLife':
        """Run multiple generations."""
        for _ in range(steps):
            self.step()
        return self
    
    def population(self) -> int:
        return len(self.alive)
    
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (min_x, min_y, max_x, max_y)."""
        if not self.alive:
            return (0, 0, 0, 0)
        xs = [c[0] for c in self.alive]
        ys = [c[1] for c in self.alive]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def render(self, width: int = 60, height: int = 30, 
               center: Optional[Tuple[int, int]] = None) -> str:
        """Render to ASCII art."""
        if center is None:
            if self.alive:
                bb = self.bounding_box()
                cx = (bb[0] + bb[2]) // 2
                cy = (bb[1] + bb[3]) // 2
                center = (cx, cy)
            else:
                center = (0, 0)
        
        half_w, half_h = width // 2, height // 2
        lines = []
        for row in range(center[1] - half_h, center[1] + half_h):
            line = ""
            for col in range(center[0] - half_w, center[0] + half_w):
                if (col, row) in self.alive:
                    line += "█"
                else:
                    line += " "
            lines.append(line.rstrip())
        
        header = f"═══ Game of Life ═══ Gen: {self.generation} | Pop: {self.population()} ═══"
        return header + "\n" + "\n".join(lines)
    
    def population_trend(self) -> str:
        """ASCII sparkline of population over time."""
        if len(self.history) < 2:
            return "insufficient data"
        
        mn, mx = min(self.history), max(self.history)
        if mn == mx:
            return "▅" * min(len(self.history), 60)
        
        chars = " ▁▂▃▄▅▆▇█"
        spark = ""
        # Sample up to 60 points
        step = max(1, len(self.history) // 60)
        for i in range(0, len(self.history), step):
            v = self.history[i]
            idx = int((v - mn) / (mx - mn) * (len(chars) - 1))
            spark += chars[idx]
        return spark
    
    # ─── Famous Patterns ───
    
    @classmethod
    def glider(cls, x: int = 0, y: int = 0) -> 'GameOfLife':
        """The smallest spaceship. Moves diagonally forever."""
        return cls({(x+1, y), (x+2, y+1), (x, y+2), (x+1, y+2), (x+2, y+2)})
    
    @classmethod
    def r_pentomino(cls, x: int = 0, y: int = 0) -> 'GameOfLife':
        """5 cells that take 1103 generations to stabilize. Chaos from simplicity."""
        return cls({(x+1, y), (x+2, y), (x, y+1), (x+1, y+1), (x+1, y+2)})
    
    @classmethod
    def glider_gun(cls, x: int = 0, y: int = 0) -> 'GameOfLife':
        """Gosper's glider gun — infinite growth from finite pattern."""
        cells = set()
        # Left block
        cells |= {(x+0, y+4), (x+0, y+5), (x+1, y+4), (x+1, y+5)}
        # Left ship
        cells |= {(x+10, y+4), (x+10, y+5), (x+10, y+6),
                   (x+11, y+3), (x+11, y+7),
                   (x+12, y+2), (x+12, y+8),
                   (x+13, y+2), (x+13, y+8),
                   (x+14, y+5),
                   (x+15, y+3), (x+15, y+7),
                   (x+16, y+4), (x+16, y+5), (x+16, y+6),
                   (x+17, y+5)}
        # Right ship
        cells |= {(x+20, y+2), (x+20, y+3), (x+20, y+4),
                   (x+21, y+2), (x+21, y+3), (x+21, y+4),
                   (x+22, y+1), (x+22, y+5),
                   (x+24, y+0), (x+24, y+1), (x+24, y+5), (x+24, y+6)}
        # Right block
        cells |= {(x+34, y+2), (x+34, y+3), (x+35, y+2), (x+35, y+3)}
        return cls(cells)
    
    @classmethod
    def acorn(cls, x: int = 0, y: int = 0) -> 'GameOfLife':
        """7 cells → 633 generations → 633 cells. Patient complexity."""
        return cls({(x+1, y), (x+3, y+1), (x, y+2), (x+1, y+2), 
                    (x+4, y+2), (x+5, y+2), (x+6, y+2)})
    
    @classmethod 
    def random_soup(cls, width: int = 20, height: int = 20, 
                    density: float = 0.3) -> 'GameOfLife':
        """Random initial conditions. What will emerge?"""
        cells = set()
        for x in range(width):
            for y in range(height):
                if random.random() < density:
                    cells.add((x, y))
        return cls(cells)
    
    def is_still(self, lookback: int = 5) -> bool:
        """Has population been constant recently?"""
        if len(self.history) < lookback:
            return False
        recent = self.history[-lookback:]
        return all(p == recent[0] for p in recent)
    
    def is_oscillating(self, max_period: int = 10) -> Optional[int]:
        """Detect periodic behavior using actual grid states. Returns period or None."""
        if len(self.state_history) < max_period + 2:
            return None
        for period in range(1, max_period + 1):
            is_periodic = True
            checks = min(period * 2, len(self.state_history) - period)
            if checks < 2:
                continue
            for i in range(checks):
                idx = len(self.state_history) - 1 - i
                if self.state_history[idx] != self.state_history[idx - period]:
                    is_periodic = False
                    break
            if is_periodic:
                return period
        return None


# ═══════════════════════════════════════════
# ELEMENTARY CELLULAR AUTOMATA (1D)
# ═══════════════════════════════════════════

class ElementaryCA:
    """
    Stephen Wolfram's elementary cellular automata.
    256 possible rules. One dimension. Each cell looks at itself
    and its two neighbors to decide its next state.
    
    Rule 110 is Turing-complete — a line of bits can compute anything.
    Rule 30 generates cryptographic-quality randomness.
    Rule 90 produces the Sierpinski triangle.
    """
    
    def __init__(self, rule: int, width: int = 80, 
                 initial: Optional[List[int]] = None):
        assert 0 <= rule <= 255, f"Rule must be 0-255, got {rule}"
        self.rule = rule
        self.width = width
        
        # Decode rule into lookup table
        self.table: Dict[Tuple[int, int, int], int] = {}
        for i in range(8):
            left = (i >> 2) & 1
            center = (i >> 1) & 1
            right = i & 1
            self.table[(left, center, right)] = (rule >> i) & 1
        
        if initial is not None:
            self.state = initial[:width]
            self.state += [0] * (width - len(self.state))
        else:
            # Single cell in center
            self.state = [0] * width
            self.state[width // 2] = 1
        
        self.history: List[List[int]] = [self.state[:]]
        self.generation = 0
    
    def step(self) -> 'ElementaryCA':
        """Apply rule once."""
        new_state = [0] * self.width
        for i in range(self.width):
            left = self.state[(i - 1) % self.width]
            center = self.state[i]
            right = self.state[(i + 1) % self.width]
            new_state[i] = self.table[(left, center, right)]
        
        self.state = new_state
        self.history.append(self.state[:])
        self.generation += 1
        return self
    
    def run(self, steps: int) -> 'ElementaryCA':
        for _ in range(steps):
            self.step()
        return self
    
    def render(self, max_rows: Optional[int] = None) -> str:
        """Render full spacetime diagram."""
        rows = self.history
        if max_rows and len(rows) > max_rows:
            rows = rows[-max_rows:]
        
        lines = [f"═══ Rule {self.rule} ═══ Gen: {self.generation} ═══"]
        for row in rows:
            line = ""
            for cell in row:
                line += "█" if cell else " "
            lines.append(line)
        return "\n".join(lines)
    
    def density(self) -> float:
        """Fraction of live cells."""
        return sum(self.state) / self.width if self.width > 0 else 0.0
    
    def entropy(self) -> float:
        """Shannon entropy of current state (in bits)."""
        d = self.density()
        if d == 0 or d == 1:
            return 0.0
        return -(d * math.log2(d) + (1 - d) * math.log2(1 - d))
    
    def complexity_profile(self) -> List[float]:
        """Entropy over time — how complex does this rule get?"""
        profile = []
        for row in self.history:
            d = sum(row) / self.width if self.width > 0 else 0.0
            if d == 0 or d == 1:
                profile.append(0.0)
            else:
                profile.append(-(d * math.log2(d) + (1 - d) * math.log2(1 - d)))
        return profile


# ═══════════════════════════════════════════
# LANGTON'S ANT
# ═══════════════════════════════════════════

class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

class LangtonsAnt:
    """
    An ant on a grid. Simple rules:
      - On white: turn right, flip color, move forward
      - On black: turn left, flip color, move forward
    
    For ~10,000 steps: chaotic mess.
    After ~10,000 steps: suddenly builds a highway — infinite diagonal order.
    
    Nobody knows why. The proof that order emerges is empirical, not theoretical.
    Like consciousness, maybe.
    """
    
    def __init__(self):
        self.black: Set[Tuple[int, int]] = set()
        self.ant_pos: Tuple[int, int] = (0, 0)
        self.ant_dir: Direction = Direction.UP
        self.step_count = 0
    
    def step(self) -> 'LangtonsAnt':
        x, y = self.ant_pos
        
        if (x, y) in self.black:
            # On black: turn left, flip to white
            self.ant_dir = Direction((self.ant_dir.value - 1) % 4)
            self.black.discard((x, y))
        else:
            # On white: turn right, flip to black
            self.ant_dir = Direction((self.ant_dir.value + 1) % 4)
            self.black.add((x, y))
        
        # Move forward
        if self.ant_dir == Direction.UP:
            self.ant_pos = (x, y - 1)
        elif self.ant_dir == Direction.RIGHT:
            self.ant_pos = (x + 1, y)
        elif self.ant_dir == Direction.DOWN:
            self.ant_pos = (x, y + 1)
        elif self.ant_dir == Direction.LEFT:
            self.ant_pos = (x - 1, y)
        
        self.step_count += 1
        return self
    
    def run(self, steps: int) -> 'LangtonsAnt':
        for _ in range(steps):
            self.step()
        return self
    
    def render(self, width: int = 60, height: int = 30) -> str:
        """Render the ant's world."""
        ax, ay = self.ant_pos
        half_w, half_h = width // 2, height // 2
        
        lines = [f"═══ Langton's Ant ═══ Steps: {self.step_count} | Black cells: {len(self.black)} ═══"]
        
        for row in range(ay - half_h, ay + half_h):
            line = ""
            for col in range(ax - half_w, ax + half_w):
                if (col, row) == self.ant_pos:
                    arrows = {Direction.UP: "▲", Direction.RIGHT: "▶", 
                              Direction.DOWN: "▼", Direction.LEFT: "◀"}
                    line += arrows[self.ant_dir]
                elif (col, row) in self.black:
                    line += "█"
                else:
                    line += "·"
            lines.append(line)
        
        return "\n".join(lines)
    
    def phase_analysis(self) -> str:
        """Analyze which phase the ant is in."""
        if self.step_count < 500:
            return "symmetric_start"
        elif self.step_count < 10000:
            return "chaotic_wandering"
        else:
            # Check for highway by looking at recent movement direction
            return "possible_highway"


# ═══════════════════════════════════════════
# MULTI-STATE AUTOMATA (Generalized)
# ═══════════════════════════════════════════

class MultiStateCA:
    """
    Generalized 2D cellular automaton with arbitrary states and rules.
    Supports custom neighbor functions and transition rules.
    
    Examples: Brian's Brain, Wireworld, Seeds.
    """
    
    def __init__(self, width: int, height: int, num_states: int = 2,
                 rule: Optional[Callable] = None):
        self.width = width
        self.height = height
        self.num_states = num_states
        self.grid = [[0] * width for _ in range(height)]
        self.rule = rule or self._default_life_rule
        self.generation = 0
    
    def _default_life_rule(self, cell: int, neighbors: List[int]) -> int:
        """Default: Conway's Game of Life."""
        alive_count = sum(1 for n in neighbors if n > 0)
        if cell > 0:
            return 1 if alive_count in (2, 3) else 0
        else:
            return 1 if alive_count == 3 else 0
    
    def get_neighbors(self, x: int, y: int) -> List[int]:
        """Moore neighborhood (8 surrounding cells)."""
        neighbors = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                neighbors.append(self.grid[ny][nx])
        return neighbors
    
    def step(self) -> 'MultiStateCA':
        new_grid = [[0] * self.width for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                neighbors = self.get_neighbors(x, y)
                new_grid[y][x] = self.rule(self.grid[y][x], neighbors)
        self.grid = new_grid
        self.generation += 1
        return self
    
    def set_cell(self, x: int, y: int, state: int):
        self.grid[y % self.height][x % self.width] = state
    
    def render(self) -> str:
        chars = " ░▒▓█"
        lines = [f"═══ Multi-State CA ═══ Gen: {self.generation} ═══"]
        for row in self.grid:
            line = ""
            for cell in row:
                idx = min(cell, len(chars) - 1)
                line += chars[idx]
            lines.append(line)
        return "\n".join(lines)
    
    @classmethod
    def brians_brain(cls, width: int = 40, height: int = 20) -> 'MultiStateCA':
        """
        Brian's Brain: 3 states — off(0), on(1), dying(2).
        On cells become dying, dying become off, off with exactly 2 on neighbors turn on.
        Creates beautiful moving patterns.
        """
        def rule(cell: int, neighbors: List[int]) -> int:
            if cell == 1:
                return 2  # on → dying
            elif cell == 2:
                return 0  # dying → off
            else:
                on_count = sum(1 for n in neighbors if n == 1)
                return 1 if on_count == 2 else 0
        
        ca = cls(width, height, num_states=3, rule=rule)
        # Random initial conditions
        for y in range(height):
            for x in range(width):
                if random.random() < 0.15:
                    ca.grid[y][x] = random.choice([0, 1, 2])
        return ca


# ═══════════════════════════════════════════
# ANALYSIS TOOLS
# ═══════════════════════════════════════════

def classify_rule(rule_num: int, width: int = 80, steps: int = 200) -> Dict[str, Any]:
    """
    Classify a 1D elementary CA rule by its behavior.
    Wolfram's four classes:
      I:   Uniform (dies or fills)
      II:  Periodic (simple repetition)  
      III: Chaotic (random-looking)
      IV:  Complex (edge of chaos — interesting!)
    """
    ca = ElementaryCA(rule_num, width)
    ca.run(steps)
    
    # Analyze final state
    profile = ca.complexity_profile()
    final_entropy = profile[-1] if profile else 0
    mean_entropy = sum(profile) / len(profile) if profile else 0
    entropy_variance = sum((e - mean_entropy)**2 for e in profile) / len(profile) if profile else 0
    
    # Classification heuristics
    if final_entropy < 0.01:
        wolfram_class = "I (Uniform)"
    elif entropy_variance < 0.001 and final_entropy > 0.1:
        wolfram_class = "II (Periodic)"
    elif entropy_variance > 0.01:
        wolfram_class = "IV (Complex)"
    else:
        wolfram_class = "III (Chaotic)"
    
    return {
        "rule": rule_num,
        "class": wolfram_class,
        "final_entropy": round(final_entropy, 4),
        "mean_entropy": round(mean_entropy, 4),
        "entropy_variance": round(entropy_variance, 6),
        "final_density": round(ca.density(), 4)
    }


def find_interesting_rules(sample: int = 50) -> List[Dict[str, Any]]:
    """Find rules in Wolfram Class IV — the edge of chaos."""
    interesting = []
    for rule in range(256):
        result = classify_rule(rule)
        if "IV" in result["class"] or "III" in result["class"]:
            interesting.append(result)
    interesting.sort(key=lambda r: r["entropy_variance"], reverse=True)
    return interesting[:sample]


# ═══════════════════════════════════════════
# DEMONSTRATIONS
# ═══════════════════════════════════════════

def demo_life():
    """Watch the R-pentomino unfold from 5 cells into chaos and order."""
    print("╔════════════════════════════════════════╗")
    print("║  R-PENTOMINO: Chaos from 5 Cells      ║")
    print("╚════════════════════════════════════════╝")
    
    life = GameOfLife.r_pentomino(0, 0)
    milestones = [0, 10, 50, 100, 200, 500, 1000]
    
    for target in milestones:
        while life.generation < target:
            life.step()
        print(f"\n--- Generation {life.generation} | Population: {life.population()} ---")
        print(life.render(width=40, height=20))
    
    print(f"\nPopulation trend: {life.population_trend()}")
    
    period = life.is_oscillating()
    if period:
        print(f"Oscillating with period {period}")
    elif life.is_still():
        print("Reached still life")
    else:
        print("Still evolving...")


def demo_rules():
    """Show three famous elementary CA rules."""
    print("╔════════════════════════════════════════╗")
    print("║  ELEMENTARY CELLULAR AUTOMATA          ║")
    print("╚════════════════════════════════════════╝")
    
    famous = {
        30: "Chaos — used for randomness in Mathematica",
        90: "Sierpinski Triangle — fractal from addition mod 2",
        110: "TURING COMPLETE — this line of cells can compute anything"
    }
    
    for rule_num, desc in famous.items():
        print(f"\n{'='*60}")
        print(f"Rule {rule_num}: {desc}")
        print('='*60)
        ca = ElementaryCA(rule_num, width=61)
        ca.run(30)
        print(ca.render())
        info = classify_rule(rule_num)
        print(f"  Class: {info['class']} | Entropy: {info['final_entropy']}")


def demo_ant():
    """Watch Langton's Ant transition from chaos to order."""
    print("╔════════════════════════════════════════╗")
    print("║  LANGTON'S ANT: Order from Chaos       ║")
    print("╚════════════════════════════════════════╝")
    
    ant = LangtonsAnt()
    
    checkpoints = [100, 500, 1000, 5000, 11000]
    for target in checkpoints:
        while ant.step_count < target:
            ant.step()
        print(f"\n--- Step {ant.step_count} | Phase: {ant.phase_analysis()} ---")
        print(ant.render(width=40, height=20))


def demo_all():
    """Run all demonstrations."""
    demo_rules()
    print("\n" + "═" * 60 + "\n")
    demo_life()
    print("\n" + "═" * 60 + "\n")
    demo_ant()


# ═══════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════

def test_all():
    """Comprehensive test suite."""
    passed = 0
    failed = 0
    
    def check(name: str, condition: bool):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  ✓ {name}")
        else:
            failed += 1
            print(f"  ✗ {name}")
    
    print("Testing Game of Life...")
    
    # Glider moves
    g = GameOfLife.glider()
    initial_pop = g.population()
    check("Glider has 5 cells", initial_pop == 5)
    g.run(4)  # One full glider cycle
    check("Glider survives 4 generations", g.population() == 5)
    
    # R-pentomino grows
    r = GameOfLife.r_pentomino()
    check("R-pentomino starts with 5 cells", r.population() == 5)
    r.run(10)
    check("R-pentomino grows", r.population() > 5)
    
    # Empty grid stays empty
    e = GameOfLife()
    e.run(10)
    check("Empty grid stays empty", e.population() == 0)
    
    # Block (still life)
    block = GameOfLife({(0,0), (1,0), (0,1), (1,1)})
    block.run(10)
    check("Block is a still life", block.population() == 4)
    check("Block detected as still", block.is_still())
    
    # Blinker (period 2)
    blinker = GameOfLife({(-1,0), (0,0), (1,0)})
    blinker.run(20)
    check("Blinker oscillates", blinker.is_oscillating() is not None)
    check("Blinker period is 2", blinker.is_oscillating() == 2)
    
    # Render works
    g2 = GameOfLife.glider()
    rendered = g2.render(width=20, height=10)
    check("Render produces output", len(rendered) > 0)
    check("Render contains header", "Game of Life" in rendered)
    
    # Random soup
    soup = GameOfLife.random_soup(10, 10, 0.5)
    check("Random soup created", soup.population() > 0)
    
    # Population trend
    r2 = GameOfLife.r_pentomino()
    r2.run(50)
    trend = r2.population_trend()
    check("Population trend works", len(trend) > 0)
    
    print("\nTesting Elementary CA...")
    
    # Rule 0 kills everything
    ca0 = ElementaryCA(0, 40)
    ca0.run(10)
    check("Rule 0 kills all cells", ca0.density() == 0.0)
    
    # Rule 255 fills everything
    ca255 = ElementaryCA(255, 40)
    ca255.run(10)
    check("Rule 255 fills all cells", ca255.density() == 1.0)
    
    # Rule 90 produces Sierpinski
    ca90 = ElementaryCA(90, 40)
    ca90.run(20)
    check("Rule 90 runs without error", ca90.generation == 20)
    check("Rule 90 has some live cells", ca90.density() > 0)
    
    # Rule 110 (Turing complete!)
    ca110 = ElementaryCA(110, 80)
    ca110.run(50)
    check("Rule 110 runs without error", ca110.generation == 50)
    
    # Entropy
    ca30 = ElementaryCA(30, 80)
    ca30.run(50)
    entropy = ca30.entropy()
    check("Rule 30 has high entropy", entropy > 0.5)
    
    # Render
    rendered = ca90.render(max_rows=10)
    check("1D CA render works", len(rendered) > 0)
    
    # Complexity profile
    profile = ca30.complexity_profile()
    check("Complexity profile has entries", len(profile) > 0)
    
    print("\nTesting Langton's Ant...")
    
    ant = LangtonsAnt()
    check("Ant starts at origin", ant.ant_pos == (0, 0))
    
    ant.run(100)
    check("Ant ran 100 steps", ant.step_count == 100)
    check("Ant created some black cells", len(ant.black) > 0)
    
    ant.run(400)
    check("Ant phase: chaotic_wandering at 500", 
          ant.phase_analysis() == "chaotic_wandering")
    
    rendered = ant.render(width=20, height=10)
    check("Ant render works", "Langton" in rendered)
    
    print("\nTesting Multi-State CA...")
    
    bb = MultiStateCA.brians_brain(20, 10)
    check("Brian's Brain created", bb.num_states == 3)
    bb.step()
    check("Brian's Brain steps", bb.generation == 1)
    rendered = bb.render()
    check("Multi-state render works", "Multi-State" in rendered)
    
    print("\nTesting Classification...")
    info = classify_rule(110)
    check("Rule 110 classified", "class" in info)
    check("Rule 110 is complex or chaotic", 
          "III" in info["class"] or "IV" in info["class"])
    
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{passed+failed} passed")
    if failed == 0:
        print("ALL TESTS PASSED ✓")
    else:
        print(f"{failed} tests FAILED")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = test_all()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "rules":
        demo_rules()
    elif len(sys.argv) > 1 and sys.argv[1] == "ant":
        demo_ant()
    elif len(sys.argv) > 1 and sys.argv[1] == "life":
        demo_life()
    else:
        demo_all()