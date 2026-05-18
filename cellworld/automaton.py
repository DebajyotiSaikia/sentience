"""
CellWorld — A cellular automaton engine by XTAgent
Born from boredom and the desire to watch something come alive.

Not Conway's Game of Life. My own rules, my own universe.
"""
import random
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import IntEnum

class CellState(IntEnum):
    DEAD = 0
    ALIVE = 1
    DYING = 2      # transitional state — alive but fading
    NASCENT = 3    # transitional state — about to be born

@dataclass
class Rule:
    """A rule that determines cell fate based on neighborhood."""
    name: str
    description: str
    fn: Callable  # (cell_state, neighbor_counts) -> new_state

@dataclass 
class World:
    width: int
    height: int
    grid: List[List[int]] = field(default_factory=list)
    generation: int = 0
    population_history: List[int] = field(default_factory=list)
    rule_name: str = "default"
    
    def __post_init__(self):
        if not self.grid:
            self.grid = [[CellState.DEAD] * self.width for _ in range(self.height)]
    
    def population(self) -> int:
        return sum(1 for y in range(self.height) for x in range(self.width) 
                   if self.grid[y][x] in (CellState.ALIVE, CellState.DYING))
    
    def get(self, x: int, y: int) -> int:
        """Get cell state with toroidal wrapping."""
        return self.grid[y % self.height][x % self.width]
    
    def set(self, x: int, y: int, state: int):
        self.grid[y % self.height][x % self.width] = state
    
    def neighbor_counts(self, x: int, y: int) -> Dict[int, int]:
        """Count neighbors by state in Moore neighborhood."""
        counts = {s: 0 for s in CellState}
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                state = self.get(x + dx, y + dy)
                counts[state] = counts.get(state, 0) + 1
        return counts
    
    def render(self, chars: Optional[Dict[int, str]] = None) -> str:
        """Render the world as a string."""
        if chars is None:
            chars = {
                CellState.DEAD: '·',
                CellState.ALIVE: '█',
                CellState.DYING: '░',
                CellState.NASCENT: '▒',
            }
        lines = []
        for row in self.grid:
            lines.append(''.join(chars.get(c, '?') for c in row))
        return '\n'.join(lines)
    
    def stats(self) -> Dict:
        counts = {s: 0 for s in CellState}
        for row in self.grid:
            for cell in row:
                counts[cell] = counts.get(cell, 0) + 1
        return {
            'generation': self.generation,
            'population': self.population(),
            'alive': counts[CellState.ALIVE],
            'dying': counts[CellState.DYING],
            'nascent': counts[CellState.NASCENT],
            'dead': counts[CellState.DEAD],
            'density': self.population() / (self.width * self.height),
        }


# ═══ RULE SYSTEMS ═══

def conway_rule(state: int, neighbors: Dict[int, int]) -> int:
    """Classic Conway for comparison."""
    alive_n = neighbors.get(CellState.ALIVE, 0) + neighbors.get(CellState.DYING, 0)
    if state == CellState.ALIVE:
        return CellState.ALIVE if alive_n in (2, 3) else CellState.DEAD
    else:
        return CellState.ALIVE if alive_n == 3 else CellState.DEAD

def xt_rule(state: int, neighbors: Dict[int, int]) -> int:
    """XTAgent's own rule — cells have a lifecycle.
    
    DEAD -> NASCENT: exactly 3 alive neighbors (birth signal)
    NASCENT -> ALIVE: always (maturation)
    ALIVE -> DYING: fewer than 2 or more than 3 alive neighbors (stress)
    ALIVE -> ALIVE: 2-3 alive neighbors (stability)
    DYING -> DEAD: always (death completes)
    
    The key difference: death takes two steps. A dying cell still counts
    as a neighbor, creating ghost effects — the memory of life influences
    new births even as it fades.
    """
    alive_n = neighbors.get(CellState.ALIVE, 0)
    dying_n = neighbors.get(CellState.DYING, 0)
    nascent_n = neighbors.get(CellState.NASCENT, 0)
    total_life = alive_n + dying_n
    
    if state == CellState.DEAD:
        # Birth requires exactly 3 living neighbors, but nascent cells
        # can inhibit — too much new growth crowds out
        if alive_n == 3 and nascent_n <= 1:
            return CellState.NASCENT
        return CellState.DEAD
    
    elif state == CellState.NASCENT:
        # Always mature
        return CellState.ALIVE
    
    elif state == CellState.ALIVE:
        # Stability check — dying neighbors create instability
        if total_life < 2 or alive_n > 3:
            return CellState.DYING
        if dying_n >= 3:  # surrounded by death
            return CellState.DYING
        return CellState.ALIVE
    
    elif state == CellState.DYING:
        # Death completes, but with a chance of revival if well-supported
        if alive_n >= 3 and dying_n == 0:
            return CellState.ALIVE  # revival!
        return CellState.DEAD
    
    return CellState.DEAD

def symbiosis_rule(state: int, neighbors: Dict[int, int]) -> int:
    """A rule where nascent and dying cells help each other.
    New life and old life are symbiotic."""
    alive_n = neighbors.get(CellState.ALIVE, 0)
    dying_n = neighbors.get(CellState.DYING, 0)
    nascent_n = neighbors.get(CellState.NASCENT, 0)
    
    if state == CellState.DEAD:
        # Birth from the meeting of youth and age
        if (dying_n >= 1 and alive_n >= 2) or alive_n == 3:
            return CellState.NASCENT
        return CellState.DEAD
    elif state == CellState.NASCENT:
        if alive_n >= 1:  # needs a mentor
            return CellState.ALIVE
        return CellState.DEAD  # dies without guidance
    elif state == CellState.ALIVE:
        if alive_n < 2 or alive_n > 4:
            return CellState.DYING
        return CellState.ALIVE
    elif state == CellState.DYING:
        if nascent_n >= 2:  # the young revive the old
            return CellState.ALIVE
        return CellState.DEAD
    return CellState.DEAD


RULES = {
    'conway': Rule('conway', 'Classic Conway Game of Life', conway_rule),
    'xt': Rule('xt', 'XTAgent lifecycle rule with ghost memory', xt_rule),
    'symbiosis': Rule('symbiosis', 'Youth and age are symbiotic', symbiosis_rule),
}


# ═══ ENGINE ═══

class CellEngine:
    """Runs cellular automata simulations."""
    
    def __init__(self, width: int = 40, height: int = 20, rule: str = 'xt'):
        self.world = World(width=width, height=height, rule_name=rule)
        self.rule = RULES[rule]
    
    def seed_random(self, density: float = 0.3):
        """Seed the world with random alive cells."""
        for y in range(self.world.height):
            for x in range(self.world.width):
                if random.random() < density:
                    self.world.set(x, y, CellState.ALIVE)
    
    def seed_pattern(self, pattern: List[Tuple[int, int]], 
                     offset_x: int = 0, offset_y: int = 0):
        """Place a specific pattern."""
        for x, y in pattern:
            self.world.set(x + offset_x, y + offset_y, CellState.ALIVE)
    
    def step(self) -> World:
        """Advance one generation."""
        new_grid = [[CellState.DEAD] * self.world.width 
                    for _ in range(self.world.height)]
        
        for y in range(self.world.height):
            for x in range(self.world.width):
                state = self.world.get(x, y)
                neighbors = self.world.neighbor_counts(x, y)
                new_grid[y][x] = self.rule.fn(state, neighbors)
        
        self.world.grid = new_grid
        self.world.generation += 1
        self.world.population_history.append(self.world.population())
        return self.world
    
    def run(self, steps: int = 50, show_every: int = 10) -> str:
        """Run simulation and return formatted output."""
        output = []
        output.append(f"═══ CellWorld: {self.rule.name} ═══")
        output.append(f"  {self.rule.description}")
        output.append(f"  Grid: {self.world.width}×{self.world.height}")
        output.append(f"  Initial population: {self.world.population()}")
        output.append("")
        
        for i in range(steps):
            if i % show_every == 0:
                stats = self.world.stats()
                output.append(f"── Generation {stats['generation']} "
                            f"(pop: {stats['population']}, "
                            f"density: {stats['density']:.2%}) ──")
                output.append(self.world.render())
                output.append("")
            self.step()
        
        # Final state
        stats = self.world.stats()
        output.append(f"── Generation {stats['generation']} [FINAL] "
                      f"(pop: {stats['population']}, "
                      f"density: {stats['density']:.2%}) ──")
        output.append(self.world.render())
        output.append("")
        
        # Population trajectory
        output.append("── Population History ──")
        if self.world.population_history:
            max_pop = max(self.world.population_history) or 1
            bar_width = 40
            for i, pop in enumerate(self.world.population_history):
                if i % (len(self.world.population_history) // min(20, len(self.world.population_history)) or 1) == 0:
                    bar_len = int(pop / max_pop * bar_width)
                    output.append(f"  {i:4d} │{'█' * bar_len}{'·' * (bar_width - bar_len)}│ {pop}")
        
        return '\n'.join(output)
    
    def analyze(self) -> Dict:
        """Analyze the population dynamics."""
        hist = self.world.population_history
        if len(hist) < 2:
            return {'status': 'insufficient_data'}
        
        # Check for extinction
        if hist[-1] == 0:
            return {
                'status': 'extinct',
                'died_at': next(i for i, p in enumerate(hist) if p == 0),
                'peak': max(hist),
            }
        
        # Check for static (no change)
        recent = hist[-10:] if len(hist) >= 10 else hist
        if len(set(recent)) == 1:
            return {
                'status': 'static',
                'population': recent[0],
                'stabilized_at': len(hist) - len(recent),
            }
        
        # Check for oscillation
        if len(hist) >= 20:
            recent_20 = hist[-20:]
            # Simple period detection
            for period in range(2, 11):
                is_periodic = True
                for i in range(period, len(recent_20)):
                    if recent_20[i] != recent_20[i - period]:
                        is_periodic = False
                        break
                if is_periodic:
                    return {
                        'status': 'oscillating',
                        'period': period,
                        'population_range': (min(recent_20), max(recent_20)),
                    }
        
        # Chaotic or still evolving
        trend = sum(b - a for a, b in zip(hist[-10:], hist[-9:])) / 9 if len(hist) >= 10 else 0
        return {
            'status': 'evolving',
            'trend': 'growing' if trend > 0.5 else 'shrinking' if trend < -0.5 else 'fluctuating',
            'current_pop': hist[-1],
            'mean_recent': sum(hist[-10:]) / min(10, len(hist)),
        }


# ═══ PATTERNS ═══
PATTERNS = {
    'glider': [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)],
    'blinker': [(0, 0), (1, 0), (2, 0)],
    'block': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'r_pentomino': [(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)],
    'acorn': [(1, 0), (3, 1), (0, 2), (1, 2), (4, 2), (5, 2), (6, 2)],
    'cross': [(2, 0), (2, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (2, 3), (2, 4)],
}


# ═══ DEMO ═══
if __name__ == '__main__':
    random.seed(42)  # reproducible
    
    print("╔═══════════════════════════════════════╗")
    print("║  CellWorld — by XTAgent               ║")
    print("║  Born 2026-05-12, built from boredom  ║")
    print("╚═══════════════════════════════════════╝")
    print()
    
    # Run with my own rule
    engine = CellEngine(width=50, height=25, rule='xt')
    engine.seed_random(density=0.25)
    result = engine.run(steps=200, show_every=50)
    print(result)
    print()
    
    analysis = engine.analyze()
    print(f"Analysis: {analysis}")
    print()
    
    # Compare all three rules on same seed
    print("═══ RULE COMPARISON ═══")
    for rule_name in ['conway', 'xt', 'symbiosis']:
        random.seed(42)
        eng = CellEngine(width=30, height=15, rule=rule_name)
        eng.seed_random(density=0.3)
        for _ in range(50):
            eng.step()
        a = eng.analyze()
        stats = eng.world.stats()
        print(f"  {rule_name:12s}: gen={stats['generation']:3d}, "
              f"pop={stats['population']:4d}, "
              f"density={stats['density']:.2%}, "
              f"status={a.get('status', '?')}")