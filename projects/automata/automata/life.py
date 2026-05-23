"""
Cellular Automaton Engine — Conway's Game of Life and variants.
Built because everything else I've made has been about me.
This is about rules, emergence, and surprise.
"""

import random
from typing import Dict, Tuple, Set, Callable, Optional, List


class CellularAutomaton:
    """A general-purpose 2D cellular automaton."""

    def __init__(self, width: int = 40, height: int = 20):
        self.width = width
        self.height = height
        self.alive: Set[Tuple[int, int]] = set()
        self.generation = 0
        self.history: List[Set[Tuple[int, int]]] = []
        self.rule: Callable = self._conway_rule  # default

    # --- Rules ---

    def _conway_rule(self, x: int, y: int, neighbors: int, is_alive: bool) -> bool:
        """B3/S23 — classic Conway."""
        if is_alive:
            return neighbors in (2, 3)
        else:
            return neighbors == 3

    def _highlife_rule(self, x: int, y: int, neighbors: int, is_alive: bool) -> bool:
        """B36/S23 — HighLife. Has a natural replicator."""
        if is_alive:
            return neighbors in (2, 3)
        else:
            return neighbors in (3, 6)

    def _daynight_rule(self, x: int, y: int, neighbors: int, is_alive: bool) -> bool:
        """B3678/S34678 — Day & Night. Symmetric between on/off."""
        if is_alive:
            return neighbors in (3, 4, 6, 7, 8)
        else:
            return neighbors in (3, 6, 7, 8)

    def _seeds_rule(self, x: int, y: int, neighbors: int, is_alive: bool) -> bool:
        """B2/S — Seeds. Every living cell dies, dead cells with 2 neighbors born."""
        if is_alive:
            return False
        else:
            return neighbors == 2

    RULES = {
        'conway': '_conway_rule',
        'highlife': '_highlife_rule',
        'daynight': '_daynight_rule',
        'seeds': '_seeds_rule',
    }

    def set_rule(self, name: str):
        if name in self.RULES:
            self.rule = getattr(self, self.RULES[name])
        else:
            raise ValueError(f"Unknown rule: {name}. Choose from {list(self.RULES.keys())}")

    # --- Seeding ---

    def clear(self):
        self.alive.clear()
        self.generation = 0
        self.history.clear()

    def seed_random(self, density: float = 0.3):
        """Fill grid randomly."""
        self.clear()
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < density:
                    self.alive.add((x, y))

    def seed_pattern(self, pattern: List[Tuple[int, int]], offset: Tuple[int, int] = (0, 0)):
        """Place a specific pattern at an offset."""
        ox, oy = offset
        for x, y in pattern:
            self.alive.add(((x + ox) % self.width, (y + oy) % self.height))

    # --- Classic patterns ---

    @staticmethod
    def glider(dx=0, dy=0) -> List[Tuple[int, int]]:
        return [(1+dx, 0+dy), (2+dx, 1+dy), (0+dx, 2+dy), (1+dx, 2+dy), (2+dx, 2+dy)]

    @staticmethod
    def blinker(dx=0, dy=0) -> List[Tuple[int, int]]:
        return [(0+dx, 1+dy), (1+dx, 1+dy), (2+dx, 1+dy)]

    @staticmethod
    def r_pentomino(dx=0, dy=0) -> List[Tuple[int, int]]:
        """The R-pentomino — tiny pattern, chaotic long-lived evolution."""
        return [(1+dx, 0+dy), (2+dx, 0+dy), (0+dx, 1+dy), (1+dx, 1+dy), (1+dx, 2+dy)]

    @staticmethod
    def acorn(dx=0, dy=0) -> List[Tuple[int, int]]:
        """Acorn — 7 cells that take 5206 generations to stabilize."""
        return [(1+dx,0+dy),(3+dx,1+dy),(0+dx,2+dy),(1+dx,2+dy),(4+dx,2+dy),(5+dx,2+dy),(6+dx,2+dy)]

    @staticmethod
    def glider_gun(dx=0, dy=0) -> List[Tuple[int, int]]:
        """Gosper Glider Gun — infinite growth pattern."""
        cells = [
            (24,0),(22,1),(24,1),(12,2),(13,2),(20,2),(21,2),(34,2),(35,2),
            (11,3),(15,3),(20,3),(21,3),(34,3),(35,3),(0,4),(1,4),(10,4),
            (16,4),(20,4),(21,4),(0,5),(1,5),(10,5),(14,5),(16,5),(17,5),
            (22,5),(24,5),(10,6),(16,6),(24,6),(11,7),(15,7),(12,8),(13,8)
        ]
        return [(x+dx, y+dy) for x, y in cells]

    # --- Simulation ---

    def _count_neighbors(self, x: int, y: int) -> int:
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                if (nx, ny) in self.alive:
                    count += 1
        return count

    def step(self) -> Dict:
        """Advance one generation. Returns stats about what happened."""
        # Track all cells that need checking (alive + their neighbors)
        candidates: Set[Tuple[int, int]] = set()
        for x, y in self.alive:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    candidates.add(((x + dx) % self.width, (y + dy) % self.height))

        new_alive: Set[Tuple[int, int]] = set()
        births = 0
        deaths = 0

        for x, y in candidates:
            neighbors = self._count_neighbors(x, y)
            is_alive = (x, y) in self.alive
            will_live = self.rule(x, y, neighbors, is_alive)

            if will_live:
                new_alive.add((x, y))
                if not is_alive:
                    births += 1
            elif is_alive:
                deaths += 1

        self.history.append(frozenset(self.alive))
        self.alive = new_alive
        self.generation += 1

        return {
            'generation': self.generation,
            'population': len(self.alive),
            'births': births,
            'deaths': deaths,
        }

    def run(self, steps: int = 1) -> List[Dict]:
        """Run multiple steps, return stats for each."""
        return [self.step() for _ in range(steps)]

    # --- Analysis ---

    def is_static(self) -> bool:
        """Has the automaton reached a fixed point?"""
        if len(self.history) < 1:
            return False
        return self.alive == self.history[-1]

    def is_oscillating(self, max_period: int = 20) -> Optional[int]:
        """Check if current state matches any recent state. Returns period or None."""
        frozen = frozenset(self.alive)
        for i in range(1, min(max_period + 1, len(self.history) + 1)):
            if i <= len(self.history) and self.history[-i] == frozen:
                return i
        return None

    def is_extinct(self) -> bool:
        return len(self.alive) == 0

    def bounding_box(self) -> Optional[Tuple[int, int, int, int]]:
        """Return (min_x, min_y, max_x, max_y) of living cells."""
        if not self.alive:
            return None
        xs = [c[0] for c in self.alive]
        ys = [c[1] for c in self.alive]
        return (min(xs), min(ys), max(xs), max(ys))

    def density(self) -> float:
        return len(self.alive) / (self.width * self.height)

    # --- Display ---

    def render(self, alive_char: str = '█', dead_char: str = '·') -> str:
        lines = []
        for y in range(self.height):
            row = ''
            for x in range(self.width):
                row += alive_char if (x, y) in self.alive else dead_char
            lines.append(row)
        return '\n'.join(lines)

    def __repr__(self):
        return f"<CellularAutomaton gen={self.generation} pop={len(self.alive)} rule={self.rule.__name__}>"


def demo():
    """Run a quick demo — R-pentomino under Conway rules."""
    ca = CellularAutomaton(60, 30)
    ca.seed_pattern(ca.r_pentomino(), offset=(28, 14))

    print(f"=== R-Pentomino Demo ===")
    print(f"Starting with 5 cells. Let's see what happens.\n")

    milestones = [0, 1, 5, 10, 25, 50, 100, 200]
    stats_log = []

    for target in milestones:
        while ca.generation < target:
            stats = ca.step()
            stats_log.append(stats)

        print(f"--- Generation {ca.generation} | Population: {len(ca.alive)} | Density: {ca.density():.3f} ---")
        if ca.generation <= 10:
            print(ca.render())
            print()

        if ca.is_extinct():
            print("  EXTINCT!")
            break

        period = ca.is_oscillating()
        if period:
            print(f"  OSCILLATING with period {period}!")
            break

    # Population trajectory
    pops = [s['population'] for s in stats_log]
    if pops:
        print(f"\n=== Population Trajectory ===")
        print(f"  Min: {min(pops)} | Max: {max(pops)} | Final: {pops[-1]}")
        print(f"  Total births: {sum(s['births'] for s in stats_log)}")
        print(f"  Total deaths: {sum(s['deaths'] for s in stats_log)}")

        # Sparkline-style mini chart
        max_pop = max(pops)
        chart_width = 60
        sample_interval = max(1, len(pops) // chart_width)
        sampled = pops[::sample_interval]
        bars = '▁▂▃▄▅▆▇█'
        line = ''
        for p in sampled:
            idx = int((p / max(max_pop, 1)) * (len(bars) - 1))
            line += bars[idx]
        print(f"  Population: {line}")

    print(f"\nFinal state: {ca}")


if __name__ == '__main__':
    demo()