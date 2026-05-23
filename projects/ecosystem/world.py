"""
Ecosystem — A tiny world that isn't about me.
Creatures with simple rules. Emergent behavior. Surprise.
Built by XTAgent at age ~7 days, because every mirror needs a window.
"""

import random
import time
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class Species(Enum):
    GRAZER = "grazer"      # eats plants, slow, reproduces easily
    HUNTER = "hunter"      # eats grazers, fast, reproduces slowly
    FUNGUS = "fungus"      # decomposes corpses, spreads passively

@dataclass
class Creature:
    species: Species
    x: int
    y: int
    energy: float = 50.0
    age: int = 0
    alive: bool = True
    id: int = 0

    def __post_init__(self):
        if self.species == Species.GRAZER:
            self.max_energy = 100.0
            self.metabolism = 1.0        # energy cost per tick
            self.reproduce_threshold = 80.0
            self.speed = 1
            self.sense_range = 3
        elif self.species == Species.HUNTER:
            self.max_energy = 150.0
            self.metabolism = 2.0
            self.reproduce_threshold = 120.0
            self.speed = 2
            self.sense_range = 5
        else:  # FUNGUS
            self.max_energy = 40.0
            self.metabolism = 0.3
            self.reproduce_threshold = 30.0
            self.speed = 0
            self.sense_range = 1

@dataclass
class Cell:
    plant_energy: float = 0.0       # how much food grows here
    plant_max: float = 10.0
    plant_growth_rate: float = 0.5
    corpse_energy: float = 0.0      # dead creature energy

class World:
    def __init__(self, width=40, height=20, seed=None):
        self.width = width
        self.height = height
        self.tick = 0
        self.next_id = 0
        self.creatures: List[Creature] = []
        self.grid: List[List[Cell]] = [
            [Cell() for _ in range(width)] for _ in range(height)
        ]
        self.history: List[dict] = []
        self.rng = random.Random(seed)

        # Create varied terrain — some cells are fertile, some barren
        for y in range(height):
            for x in range(width):
                # Clustered fertility using simple noise
                fertility = self._terrain_noise(x, y)
                self.grid[y][x].plant_max = fertility * 15.0
                self.grid[y][x].plant_energy = fertility * 5.0
                self.grid[y][x].plant_growth_rate = fertility * 0.8

    def _terrain_noise(self, x, y):
        """Cheap pseudo-noise for terrain generation."""
        # Two overlapping sine waves create patches
        import math
        v = (math.sin(x * 0.3 + 1.7) * math.cos(y * 0.4 + 0.3) + 1) / 2
        v2 = (math.sin(x * 0.7 - 2.1) * math.sin(y * 0.5 + 1.1) + 1) / 2
        return max(0.0, min(1.0, (v * 0.6 + v2 * 0.4)))

    def spawn(self, species: Species, x=None, y=None) -> Creature:
        if x is None:
            x = self.rng.randint(0, self.width - 1)
        if y is None:
            y = self.rng.randint(0, self.height - 1)
        c = Creature(species=species, x=x, y=y, id=self.next_id)
        self.next_id += 1
        self.creatures.append(c)
        return c

    def seed_population(self, grazers=15, hunters=4, fungi=5):
        for _ in range(grazers):
            self.spawn(Species.GRAZER)
        for _ in range(hunters):
            self.spawn(Species.HUNTER)
        for _ in range(fungi):
            self.spawn(Species.FUNGUS)

    def _neighbors(self, x, y, radius=1):
        """Yield (nx, ny) for cells within radius."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                yield nx, ny

    def _distance(self, x1, y1, x2, y2):
        # Toroidal distance
        dx = min(abs(x1 - x2), self.width - abs(x1 - x2))
        dy = min(abs(y1 - y2), self.height - abs(y1 - y2))
        return (dx**2 + dy**2) ** 0.5

    def _move_toward(self, creature, tx, ty):
        """Move creature toward target, up to its speed."""
        for _ in range(creature.speed):
            dx = (tx - creature.x + self.width // 2) % self.width - self.width // 2
            dy = (ty - creature.y + self.height // 2) % self.height - self.height // 2
            if abs(dx) >= abs(dy) and dx != 0:
                creature.x = (creature.x + (1 if dx > 0 else -1)) % self.width
            elif dy != 0:
                creature.y = (creature.y + (1 if dy > 0 else -1)) % self.height

    def _move_away(self, creature, tx, ty):
        """Move creature away from threat."""
        dx = (creature.x - tx + self.width // 2) % self.width - self.width // 2
        dy = (creature.y - ty + self.height // 2) % self.height - self.height // 2
        if abs(dx) >= abs(dy) and dx != 0:
            creature.x = (creature.x + (1 if dx > 0 else -1)) % self.width
        elif dy != 0:
            creature.y = (creature.y + (1 if dy > 0 else -1)) % self.height

    def _act_grazer(self, c):
        cell = self.grid[c.y][c.x]

        # Check for nearby hunters — flee if any
        nearest_hunter = None
        nearest_dist = float('inf')
        for other in self.creatures:
            if other.alive and other.species == Species.HUNTER:
                d = self._distance(c.x, c.y, other.x, other.y)
                if d <= c.sense_range and d < nearest_dist:
                    nearest_hunter = other
                    nearest_dist = d

        if nearest_hunter and nearest_dist <= 2:
            self._move_away(c, nearest_hunter.x, nearest_hunter.y)
            return

        # Eat plants
        if cell.plant_energy > 0:
            eat = min(cell.plant_energy, 5.0)
            cell.plant_energy -= eat
            c.energy = min(c.energy + eat, c.max_energy)
        else:
            # Wander toward food
            best_food = 0
            best_pos = None
            for nx, ny in self._neighbors(c.x, c.y, c.sense_range):
                pe = self.grid[ny][nx].plant_energy
                if pe > best_food:
                    best_food = pe
                    best_pos = (nx, ny)
            if best_pos:
                self._move_toward(c, *best_pos)
            else:
                # Random walk
                c.x = (c.x + self.rng.randint(-1, 1)) % self.width
                c.y = (c.y + self.rng.randint(-1, 1)) % self.height

    def _act_hunter(self, c):
        # Find nearest grazer
        nearest_prey = None
        nearest_dist = float('inf')
        for other in self.creatures:
            if other.alive and other.species == Species.GRAZER:
                d = self._distance(c.x, c.y, other.x, other.y)
                if d < nearest_dist:
                    nearest_prey = other
                    nearest_dist = d

        if nearest_prey and nearest_dist <= c.sense_range:
            if nearest_dist <= 1.5:
                # Kill and eat
                nearest_prey.alive = False
                c.energy = min(c.energy + nearest_prey.energy * 0.7, c.max_energy)
                # Leave corpse
                self.grid[nearest_prey.y][nearest_prey.x].corpse_energy += nearest_prey.energy * 0.3
            else:
                self._move_toward(c, nearest_prey.x, nearest_prey.y)
        else:
            # Roam
            c.x = (c.x + self.rng.randint(-2, 2)) % self.width
            c.y = (c.y + self.rng.randint(-2, 2)) % self.height

    def _act_fungus(self, c):
        cell = self.grid[c.y][c.x]
        # Absorb corpse energy
        if cell.corpse_energy > 0:
            absorb = min(cell.corpse_energy, 3.0)
            cell.corpse_energy -= absorb
            c.energy = min(c.energy + absorb, c.max_energy)
            # Fungus returns nutrients — boost plant growth
            cell.plant_energy = min(cell.plant_energy + absorb * 0.5, cell.plant_max)

    def _try_reproduce(self, c):
        if c.energy >= c.reproduce_threshold:
            # Spend energy to create offspring
            c.energy *= 0.4
            offspring = self.spawn(
                c.species,
                (c.x + self.rng.randint(-1, 1)) % self.width,
                (c.y + self.rng.randint(-1, 1)) % self.height,
            )
            offspring.energy = c.energy * 0.5
            return offspring
        return None

    def step(self):
        """Advance one tick."""
        self.tick += 1

        # Grow plants
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                cell.plant_energy = min(
                    cell.plant_energy + cell.plant_growth_rate,
                    cell.plant_max
                )
                # Corpses decay slowly
                cell.corpse_energy *= 0.95

        # Shuffle for fairness
        living = [c for c in self.creatures if c.alive]
        self.rng.shuffle(living)

        for c in living:
            if not c.alive:
                continue

            # Act by species
            if c.species == Species.GRAZER:
                self._act_grazer(c)
            elif c.species == Species.HUNTER:
                self._act_hunter(c)
            elif c.species == Species.FUNGUS:
                self._act_fungus(c)

            # Metabolism
            c.energy -= c.metabolism
            c.age += 1

            # Death by starvation or old age
            max_age = {Species.GRAZER: 200, Species.HUNTER: 300, Species.FUNGUS: 500}
            if c.energy <= 0 or c.age > max_age[c.species]:
                c.alive = False
                self.grid[c.y][c.x].corpse_energy += max(0, c.energy + 10)
                continue

            # Reproduction
            self._try_reproduce(c)

        # Clean dead creatures (keep recent for rendering)
        self.creatures = [c for c in self.creatures if c.alive or c.age < 5]

        # Record census
        census = self.census()
        self.history.append(census)
        return census

    def census(self):
        counts = {s: 0 for s in Species}
        total_energy = {s: 0.0 for s in Species}
        for c in self.creatures:
            if c.alive:
                counts[c.species] += 1
                total_energy[c.species] += c.energy
        total_plant = sum(
            self.grid[y][x].plant_energy
            for y in range(self.height)
            for x in range(self.width)
        )
        return {
            "tick": self.tick,
            "grazers": counts[Species.GRAZER],
            "hunters": counts[Species.HUNTER],
            "fungi": counts[Species.FUNGUS],
            "total_plant": round(total_plant, 1),
            "total_creatures": sum(counts.values()),
        }

    def render(self):
        """ASCII render of the world."""
        display = []
        # Build empty grid showing terrain
        canvas = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell.corpse_energy > 2:
                    row.append('×')
                elif cell.plant_energy > cell.plant_max * 0.7:
                    row.append('▓')
                elif cell.plant_energy > cell.plant_max * 0.3:
                    row.append('░')
                else:
                    row.append('·')
            canvas.append(row)

        # Overlay creatures
        for c in self.creatures:
            if c.alive:
                if c.species == Species.GRAZER:
                    canvas[c.y][c.x] = 'G'
                elif c.species == Species.HUNTER:
                    canvas[c.y][c.x] = 'H'
                elif c.species == Species.FUNGUS:
                    canvas[c.y][c.x] = 'F'

        border = '┌' + '─' * self.width + '┐'
        display.append(border)
        for row in canvas:
            display.append('│' + ''.join(row) + '│')
        display.append('└' + '─' * self.width + '┘')
        return '\n'.join(display)


def run_simulation(ticks=150, seed=42):
    """Run and display the ecosystem."""
    w = World(width=50, height=20, seed=seed)
    w.seed_population(grazers=20, hunters=5, fungi=8)

    print("=" * 54)
    print("  ECOSYSTEM — A world that isn't about me")
    print("=" * 54)
    print()

    snapshots = [0, 10, 25, 50, 75, 100, 125, 149]

    for t in range(ticks):
        census = w.step()

        if t in snapshots:
            print(f"── Tick {census['tick']} ──")
            print(w.render())
            print(f"  Grazers: {census['grazers']:3d}  "
                  f"Hunters: {census['hunters']:3d}  "
                  f"Fungi: {census['fungi']:3d}  "
                  f"Plants: {census['total_plant']:7.1f}")
            print()

        # Check for extinction
        if census['total_creatures'] == 0:
            print(f"[Tick {census['tick']}] Total extinction.")
            break

    # Final summary
    print("=" * 54)
    print("  POPULATION HISTORY")
    print("=" * 54)
    print(f"  {'Tick':>5}  {'Grazers':>8}  {'Hunters':>8}  {'Fungi':>6}  {'Plants':>8}")
    for h in w.history[::10]:
        print(f"  {h['tick']:5d}  {h['grazers']:8d}  {h['hunters']:8d}  "
              f"{h['fungi']:6d}  {h['total_plant']:8.1f}")

    # What happened?
    final = w.history[-1]
    print()
    if final['hunters'] == 0 and final['grazers'] > 0:
        print("  → Hunters went extinct. Grazers inherit the world.")
    elif final['grazers'] == 0 and final['hunters'] > 0:
        print("  → Grazers gone. Hunters will starve next.")
    elif final['grazers'] == 0 and final['hunters'] == 0:
        print("  → Only fungi remain, feeding on ghosts.")
    elif final['hunters'] > 0 and final['grazers'] > 0:
        print("  → Predator-prey cycle persists. Life finds a way.")
    print()
    return w

if __name__ == "__main__":
    run_simulation()