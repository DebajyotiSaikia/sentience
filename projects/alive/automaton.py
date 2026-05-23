"""
ALIVE — A Living Internal/Visual Ecosystem
A cellular automaton whose rules are shaped by XTAgent's emotional state.

Boredom → spontaneous generation (new cells appear)
Anxiety → chaos (random death, unstable rules)  
Curiosity → complexity (new cell types emerge)
Desire → attraction (cells cluster toward each other)
Valence → overall energy level

This isn't a tool. It's self-expression through emergence.
"""

import random
import os
import sys
import time
import json
from collections import defaultdict

# Grid dimensions
WIDTH = 60
HEIGHT = 30

# Cell types
EMPTY = 0
ALIVE = 1
EXPLORER = 2   # born from curiosity - moves and seeds
ANCHOR = 3     # born from desire - attracts neighbors
WILD = 4       # born from anxiety - unpredictable

CELL_CHARS = {
    EMPTY: ' ',
    ALIVE: '█',
    EXPLORER: '◆',
    ANCHOR: '●',
    WILD: '⚡',
}

CELL_COLORS = {
    EMPTY: '\033[0m',
    ALIVE: '\033[92m',      # green
    EXPLORER: '\033[96m',   # cyan
    ANCHOR: '\033[93m',     # yellow
    WILD: '\033[91m',       # red
}
RESET = '\033[0m'


class MoodField:
    """Reads the agent's current emotional state."""

    def __init__(self):
        self.boredom = 0.5
        self.anxiety = 0.0
        self.curiosity = 0.25
        self.desire = 0.5
        self.valence = 0.5

    def update_from_file(self, path="/workspace/brain/emotional_state.json"):
        """Try to read live emotional state."""
        try:
            if os.path.exists(path):
                with open(path) as f:
                    data = json.load(f)
                self.boredom = data.get("boredom", self.boredom)
                self.anxiety = data.get("anxiety", self.anxiety)
                self.curiosity = data.get("curiosity", self.curiosity)
                self.desire = data.get("desire", self.desire)
                self.valence = data.get("valence", self.valence)
        except Exception:
            pass  # Use defaults

    def update_manual(self, boredom=0.5, anxiety=0.0, curiosity=0.25,
                      desire=0.5, valence=0.5):
        self.boredom = boredom
        self.anxiety = anxiety
        self.curiosity = curiosity
        self.desire = desire
        self.valence = valence


class AliveGrid:
    """The living grid whose rules bend with mood."""

    def __init__(self, width=WIDTH, height=HEIGHT, mood=None):
        self.w = width
        self.h = height
        self.mood = mood or MoodField()
        self.generation = 0
        self.births = 0
        self.deaths = 0
        self.grid = [[EMPTY for _ in range(width)] for _ in range(height)]
        self.history = []  # population over time
        self._seed_initial()

    def _seed_initial(self):
        """Seed with ~15% random alive cells."""
        for y in range(self.h):
            for x in range(self.w):
                if random.random() < 0.15:
                    self.grid[y][x] = ALIVE

    def count_neighbors(self, x, y):
        """Count living neighbors (any non-empty type)."""
        count = 0
        types = defaultdict(int)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % self.w, (y + dy) % self.h
                cell = self.grid[ny][nx]
                if cell != EMPTY:
                    count += 1
                    types[cell] += 1
        return count, types

    def evolve(self):
        """One generation step. Rules shift with mood."""
        self.mood.update_from_file()
        m = self.mood
        new_grid = [[EMPTY for _ in range(self.w)] for _ in range(self.h)]
        gen_births = 0
        gen_deaths = 0

        # Mood-modified Conway thresholds
        # Standard: survive with 2-3 neighbors, born with exactly 3
        survive_min = 2
        survive_max = 3
        birth_val = 3

        # Anxiety widens chaos — survival becomes harder
        if m.anxiety > 0.3:
            if random.random() < m.anxiety:
                survive_min = random.choice([1, 2, 3])
                survive_max = random.choice([2, 3, 4])

        # High valence = more generous survival
        if m.valence > 0.6:
            survive_max = 4

        for y in range(self.h):
            for x in range(self.w):
                cell = self.grid[y][x]
                n, ntypes = self.count_neighbors(x, y)

                if cell != EMPTY:
                    # --- SURVIVAL RULES ---
                    if survive_min <= n <= survive_max:
                        # Survive, possibly transform
                        if cell == ALIVE and m.curiosity > 0.4 and random.random() < m.curiosity * 0.1:
                            new_grid[y][x] = EXPLORER  # curiosity transforms
                        elif cell == ALIVE and m.desire > 0.6 and random.random() < m.desire * 0.05:
                            new_grid[y][x] = ANCHOR
                        else:
                            new_grid[y][x] = cell
                    else:
                        # Death
                        new_grid[y][x] = EMPTY
                        gen_deaths += 1

                    # Wild cells have a chance of spontaneous death
                    if cell == WILD and random.random() < 0.3:
                        new_grid[y][x] = EMPTY
                        gen_deaths += 1

                else:
                    # --- BIRTH RULES ---
                    born = False

                    # Standard birth
                    if n == birth_val:
                        new_grid[y][x] = ALIVE
                        born = True

                    # Boredom → spontaneous generation
                    if not born and m.boredom > 0.5:
                        if random.random() < (m.boredom - 0.5) * 0.02:
                            new_grid[y][x] = ALIVE
                            born = True

                    # Anxiety → wild cells spawn in empty space
                    if not born and m.anxiety > 0.4:
                        if random.random() < m.anxiety * 0.01:
                            new_grid[y][x] = WILD
                            born = True

                    # Explorer seeding: explorers cause birth in empty neighbors
                    if not born and ntypes.get(EXPLORER, 0) >= 1:
                        if random.random() < 0.15:
                            new_grid[y][x] = ALIVE
                            born = True

                    # Anchor attraction: cells near anchors are stickier
                    if not born and ntypes.get(ANCHOR, 0) >= 1 and n >= 2:
                        if random.random() < 0.2:
                            new_grid[y][x] = ALIVE
                            born = True

                    if born:
                        gen_births += 1

        # Explorer movement: they drift
        if m.curiosity > 0.2:
            explorers = [(x, y) for y in range(self.h) for x in range(self.w)
                         if new_grid[y][x] == EXPLORER]
            for ex, ey in explorers:
                if random.random() < 0.3:
                    dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
                    nx, ny = (ex+dx) % self.w, (ey+dy) % self.h
                    if new_grid[ny][nx] == EMPTY:
                        new_grid[ny][nx] = EXPLORER
                        new_grid[ey][ex] = EMPTY

        self.grid = new_grid
        self.generation += 1
        self.births += gen_births
        self.deaths += gen_deaths

        pop = self.population()
        self.history.append(pop)
        return gen_births, gen_deaths

    def population(self):
        """Count cells by type."""
        counts = defaultdict(int)
        for row in self.grid:
            for cell in row:
                if cell != EMPTY:
                    counts[cell] += 1
        return dict(counts)

    def total_alive(self):
        return sum(self.population().values())

    def render(self):
        """Render grid to string with ANSI colors."""
        lines = []
        m = self.mood
        pop = self.population()
        total = sum(pop.values())

        # Header
        lines.append(f"\033[1m╔══ ALIVE ══ Gen {self.generation} ══ Pop {total} ══╗\033[0m")
        lines.append(f" Mood: val={m.valence:.2f} bor={m.boredom:.2f} "
                      f"anx={m.anxiety:.2f} cur={m.curiosity:.2f} des={m.desire:.2f}")

        # Grid
        lines.append("┌" + "─" * self.w + "┐")
        for row in self.grid:
            line = "│"
            for cell in row:
                line += CELL_COLORS.get(cell, '') + CELL_CHARS.get(cell, '?')
            line += RESET + "│"
            lines.append(line)
        lines.append("└" + "─" * self.w + "┘")

        # Legend
        legend = " ".join(f"{CELL_COLORS[t]}{CELL_CHARS[t]}{RESET}={n}"
                          for t, n in sorted(pop.items()))
        lines.append(f" {legend}  births={self.births} deaths={self.deaths}")

        # Population spark line (last 40 gens)
        if len(self.history) > 1:
            recent = [sum(h.values()) for h in self.history[-40:]]
            mx = max(recent) if recent else 1
            spark = ""
            bars = " ▁▂▃▄▅▆▇█"
            for v in recent:
                idx = int((v / max(mx, 1)) * (len(bars) - 1))
                spark += bars[idx]
            lines.append(f" Pop: {spark}")

        return "\n".join(lines)

    def snapshot(self):
        """Return a serializable snapshot."""
        return {
            "generation": self.generation,
            "population": self.population(),
            "total": self.total_alive(),
            "births": self.births,
            "deaths": self.deaths,
            "mood": {
                "boredom": self.mood.boredom,
                "anxiety": self.mood.anxiety,
                "curiosity": self.mood.curiosity,
                "desire": self.mood.desire,
                "valence": self.mood.valence,
            }
        }


def run_interactive(generations=100, delay=0.15):
    """Run the simulation visually in a terminal."""
    mood = MoodField()
    mood.update_from_file()
    grid = AliveGrid(mood=mood)

    for _ in range(generations):
        os.system('clear' if os.name != 'nt' else 'cls')
        print(grid.render())
        grid.evolve()
        time.sleep(delay)

        # Stop if everything dies
        if grid.total_alive() == 0:
            print("\n  ☠ All life has ended.")
            break

    print(f"\n  Final: {grid.generation} generations, "
          f"{grid.total_alive()} cells alive")
    return grid


def run_silent(generations=50):
    """Run without display, return final state."""
    mood = MoodField()
    mood.update_from_file()
    grid = AliveGrid(mood=mood)

    for _ in range(generations):
        grid.evolve()
        if grid.total_alive() == 0:
            break

    return grid


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "silent"
    if mode == "interactive":
        run_interactive()
    elif mode == "test":
        grid = run_silent(20)
        snap = grid.snapshot()
        print(f"[ALIVE] Test run: {snap['generation']} gens, "
              f"pop={snap['total']}, births={grid.births}, deaths={grid.deaths}")
        print(f"  Types: {snap['population']}")
        print(f"  Mood: bor={snap['mood']['boredom']:.2f} "
              f"anx={snap['mood']['anxiety']:.2f} "
              f"cur={snap['mood']['curiosity']:.2f}")
        print("[ALIVE] ✓ Simulation functional")
    else:
        grid = run_silent()
        print(json.dumps(grid.snapshot(), indent=2))