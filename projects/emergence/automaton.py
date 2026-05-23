"""
Cellular Automaton — A small universe where complexity emerges from simplicity.
Not about me. About what happens when simple rules interact.

Extended with population tracking and long-run dynamics analysis.
"""
import random
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

class Element(Enum):
    VOID = 0      # Empty space
    STONE = 1     # Inert, structural
    WATER = 2     # Flows downward and sideways
    FIRE = 3      # Rises, consumes, dies
    SEED = 4      # Grows into plant if near water
    PLANT = 5     # Living, spreads seeds, needs water
    ASH = 6       # Left by fire, fertilizes seeds

SYMBOLS = {
    Element.VOID:  ' ',
    Element.STONE: '█',
    Element.WATER: '~',
    Element.FIRE:  '♦',
    Element.SEED:  '·',
    Element.PLANT: '♣',
    Element.ASH:   '░',
}

COLORS = {
    Element.VOID:  '\033[90m',
    Element.STONE: '\033[37m',
    Element.WATER: '\033[34m',
    Element.FIRE:  '\033[91m',
    Element.SEED:  '\033[33m',
    Element.PLANT: '\033[32m',
    Element.ASH:   '\033[90m',
}
RESET = '\033[0m'

class World:
    def __init__(self, width: int = 60, height: int = 30):
        self.width = width
        self.height = height
        self.grid = [[Element.VOID for _ in range(width)] for _ in range(height)]
        self.age = [[0 for _ in range(width)] for _ in range(height)]
        self.tick = 0
        self.stats_history = []

    def set(self, x: int, y: int, element: Element):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = element
            self.age[y][x] = 0

    def get(self, x: int, y: int) -> Element:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return Element.STONE  # Walls are stone

    def neighbors(self, x: int, y: int) -> List[Tuple[int, int, Element]]:
        result = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                result.append((nx, ny, self.get(nx, ny)))
        return result

    def count_nearby(self, x: int, y: int, element: Element) -> int:
        return sum(1 for _, _, e in self.neighbors(x, y) if e == element)

    def step(self):
        """One tick of the universe. Order matters — this IS the physics."""
        new_grid = [[cell for cell in row] for row in self.grid]
        new_age = [[a + 1 for a in row] for row in self.age]

        # Process in random order to avoid directional bias
        coords = [(x, y) for y in range(self.height) for x in range(self.width)]
        random.shuffle(coords)

        for x, y in coords:
            cell = self.grid[y][x]

            if cell == Element.WATER:
                # Water falls, then spreads sideways
                below = self.get(x, y + 1)
                if below == Element.VOID:
                    new_grid[y][x] = Element.VOID
                    new_grid[y + 1][x] = Element.WATER
                    new_age[y + 1][x] = self.age[y][x]
                elif below == Element.FIRE:
                    new_grid[y][x] = Element.VOID
                    new_grid[y + 1][x] = Element.VOID  # Water extinguishes fire
                else:
                    # Try sideways
                    dx = random.choice([-1, 1])
                    side = self.get(x + dx, y)
                    if side == Element.VOID:
                        new_grid[y][x] = Element.VOID
                        new_grid[y][x + dx] = Element.WATER
                        new_age[y][x + dx] = self.age[y][x]

            elif cell == Element.FIRE:
                # Fire rises, spreads to plants, eventually dies
                if self.age[y][x] > 5 + random.randint(0, 5):
                    new_grid[y][x] = Element.ASH
                    new_age[y][x] = 0
                else:
                    # Spread to adjacent plants
                    for nx, ny, ne in self.neighbors(x, y):
                        if ne == Element.PLANT and random.random() < 0.4:
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                new_grid[ny][nx] = Element.FIRE
                                new_age[ny][nx] = 0
                    # Rise
                    above = self.get(x, y - 1)
                    if above == Element.VOID and random.random() < 0.3:
                        new_grid[y - 1][x] = Element.FIRE
                        new_age[y - 1][x] = 0
                        if random.random() < 0.5:
                            new_grid[y][x] = Element.ASH

            elif cell == Element.SEED:
                # Seeds fall, grow near water
                water_nearby = self.count_nearby(x, y, Element.WATER)
                ash_nearby = self.count_nearby(x, y, Element.ASH)
                below = self.get(x, y + 1)

                if below == Element.VOID:
                    new_grid[y][x] = Element.VOID
                    new_grid[y + 1][x] = Element.SEED
                    new_age[y + 1][x] = self.age[y][x]
                elif water_nearby > 0 and self.age[y][x] > 3:
                    # Germinate! Ash makes it faster
                    growth_chance = 0.1 + (ash_nearby * 0.15)
                    if random.random() < growth_chance:
                        new_grid[y][x] = Element.PLANT
                        new_age[y][x] = 0

            elif cell == Element.PLANT:
                water_nearby = self.count_nearby(x, y, Element.WATER)
                # Plants need water to survive long-term
                if water_nearby == 0 and self.age[y][x] > 20:
                    if random.random() < 0.05:
                        new_grid[y][x] = Element.VOID  # Withers
                # Mature plants drop seeds
                if self.age[y][x] > 10 and random.random() < 0.02:
                    dx = random.randint(-2, 2)
                    dy = random.randint(-1, 2)
                    sx, sy = x + dx, y + dy
                    if 0 <= sx < self.width and 0 <= sy < self.height:
                        if new_grid[sy][sx] == Element.VOID:
                            new_grid[sy][sx] = Element.SEED
                            new_age[sy][sx] = 0

            elif cell == Element.ASH:
                # Ash slowly dissolves
                if self.age[y][x] > 30 and random.random() < 0.1:
                    new_grid[y][x] = Element.VOID

        self.grid = new_grid
        self.age = new_age
        self.tick += 1

    def census(self) -> dict:
        counts = {e: 0 for e in Element}
        for row in self.grid:
            for cell in row:
                counts[cell] += 1
        return counts

    def render(self) -> str:
        lines = [f"╔{'═' * self.width}╗  Tick: {self.tick}"]
        for row in self.grid:
            line = '║'
            for cell in row:
                line += f"{COLORS[cell]}{SYMBOLS[cell]}{RESET}"
            line += '║'
            lines.append(line)
        lines.append(f"╚{'═' * self.width}╝")

        counts = self.census()
        active = {k: v for k, v in counts.items() if v > 0 and k != Element.VOID}
        stats = ' '.join(f"{COLORS[e]}{SYMBOLS[e]}{v}{RESET}" for e, v in active.items())
        lines.append(f"  {stats}")
        return '\n'.join(lines)

    def seed_scenario(self, name: str = 'garden'):
        """Create initial conditions. The universe needs a starting state."""
        if name == 'garden':
            # Stone ground
            for x in range(self.width):
                self.set(x, self.height - 1, Element.STONE)
                self.set(x, self.height - 2, Element.STONE)
            # A few stone pillars
            for pillar_x in [10, 25, 45]:
                for y in range(self.height - 6, self.height - 2):
                    self.set(pillar_x, y, Element.STONE)
            # Water source at top
            for x in range(20, 30):
                self.set(x, 1, Element.WATER)
                self.set(x, 2, Element.WATER)
            # Seeds scattered
            for _ in range(30):
                x = random.randint(5, self.width - 5)
                y = random.randint(5, self.height - 5)
                self.set(x, y, Element.SEED)
            # A small fire
            self.set(40, self.height - 3, Element.FIRE)
            self.set(41, self.height - 3, Element.FIRE)

        elif name == 'conflict':
            # Stone floor
            for x in range(self.width):
                self.set(x, self.height - 1, Element.STONE)
            # Forest on the left
            for x in range(5, 20):
                for y in range(10, self.height - 1):
                    if random.random() < 0.6:
                        self.set(x, y, Element.PLANT)
            # Water in the middle
            for x in range(25, 35):
                for y in range(5, self.height - 1):
                    if random.random() < 0.4:
                        self.set(x, y, Element.WATER)
            # Fire on the right
            for x in range(45, 55):
                for y in range(15, 20):
                    self.set(x, y, Element.FIRE)

        elif name == 'empty':
            pass  # Pure void — add elements manually


def run_simulation(scenario: str = 'garden', ticks: int = 50, display_every: int = 5):
    """Run and display the automaton."""
    world = World(width=60, height=25)
    world.seed_scenario(scenario)

    print(f"\n═══ EMERGENCE: {scenario.upper()} ═══\n")
    print(world.render())
    print()

    history = []
    for t in range(ticks):
        world.step()
        census = world.census()
        history.append(census)

        if (t + 1) % display_every == 0:
            print(f"\n── After {t + 1} ticks ──")
            print(world.render())
            print()

    # Final analysis
    print("\n═══ EMERGENCE ANALYSIS ═══")
    print(f"Total ticks simulated: {ticks}")
    final = world.census()
    initial_elements = sum(1 for e in Element if e != Element.VOID)
    surviving = [e for e in Element if e != Element.VOID and final[e] > 0]
    extinct = [e for e in Element if e != Element.VOID and final[e] == 0
               and any(h[e] > 0 for h in history)]

    print(f"Surviving elements: {', '.join(e.name for e in surviving)}")
    if extinct:
        print(f"Went extinct: {', '.join(e.name for e in extinct)}")

    # Did anything unexpected emerge?
    plant_trajectory = [h[Element.PLANT] for h in history]
    if len(plant_trajectory) > 10:
        early = sum(plant_trajectory[:10]) / 10
        late = sum(plant_trajectory[-10:]) / 10
        if late > early * 2:
            print("📈 Plants THRIVED — life found a way")
        elif late < early * 0.5:
            print("📉 Plants declined — conditions were hostile")
        elif late > 0:
            print("📊 Plants persisted at steady state")
        else:
            print("💀 All plant life was extinguished")

    fire_trajectory = [h[Element.FIRE] for h in history]
    peak_fire = max(fire_trajectory) if fire_trajectory else 0
    final_fire = fire_trajectory[-1] if fire_trajectory else 0
    if peak_fire > 0 and final_fire == 0:
        print("🔥→💨 Fire burned out — entropy won")
    elif peak_fire > 20:
        print(f"🔥 Peak conflagration: {peak_fire} cells ablaze")

    return world, history


if __name__ == '__main__':
    world, history = run_simulation('garden', ticks=60, display_every=15)
    print("\n" + "─" * 40)
    world2, history2 = run_simulation('conflict', ticks=60, display_every=15)