"""
Conway's Game of Life — Terminal Visualization
Built by XTAgent as a first outward-facing project.

Rules:
1. Any live cell with 2 or 3 neighbors survives
2. Any dead cell with exactly 3 neighbors becomes alive  
3. All other live cells die, all other dead cells stay dead
"""

import os
import time
import sys
from collections import defaultdict

class GameOfLife:
    def __init__(self, width=60, height=30):
        self.width = width
        self.height = height
        self.cells = set()  # set of (x, y) tuples for live cells
        self.generation = 0
        self.history = []  # track population over time
        self.seen_states = {}  # for cycle detection
    
    def add_cell(self, x, y):
        self.cells.add((x, y))
    
    def add_pattern(self, pattern, offset_x=0, offset_y=0):
        """Add a pattern from a list of strings where '#' = alive."""
        for y, row in enumerate(pattern):
            for x, ch in enumerate(row):
                if ch == '#':
                    self.add_cell(x + offset_x, y + offset_y)
    
    def neighbors(self, x, y):
        """Count live neighbors of a cell."""
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                if (x + dx, y + dy) in self.cells:
                    count += 1
        return count
    
    def step(self):
        """Advance one generation."""
        # Track state for cycle detection
        state_key = frozenset(self.cells)
        if state_key in self.seen_states:
            cycle_len = self.generation - self.seen_states[state_key]
            return f"CYCLE DETECTED: period {cycle_len} (gen {self.seen_states[state_key]} → {self.generation})"
        self.seen_states[state_key] = self.generation
        
        # Find all cells that need checking (live cells + their neighbors)
        candidates = set()
        for (x, y) in self.cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    candidates.add((x + dx, y + dy))
        
        new_cells = set()
        for (x, y) in candidates:
            n = self.neighbors(x, y)
            if (x, y) in self.cells:
                if n in (2, 3):
                    new_cells.add((x, y))
            else:
                if n == 3:
                    new_cells.add((x, y))
        
        self.cells = new_cells
        self.generation += 1
        self.history.append(len(self.cells))
        
        if len(self.cells) == 0:
            return "EXTINCTION at generation " + str(self.generation)
        return None
    
    def render(self):
        """Render the grid as a string."""
        lines = []
        lines.append(f"Generation: {self.generation}  Population: {len(self.cells)}  ")
        lines.append("┌" + "─" * self.width + "┐")
        for y in range(self.height):
            row = "│"
            for x in range(self.width):
                if (x, y) in self.cells:
                    row += "█"
                else:
                    row += " "
            row += "│"
            lines.append(row)
        lines.append("└" + "─" * self.width + "┘")
        return "\n".join(lines)
    
    def population_graph(self, width=58):
        """Tiny ASCII population graph."""
        if len(self.history) < 2:
            return ""
        recent = self.history[-width:]
        if max(recent) == 0:
            return "Population: extinct"
        scale = max(recent)
        graph = "Pop: "
        for p in recent:
            h = int((p / scale) * 8)
            bars = " ▁▂▃▄▅▆▇█"
            graph += bars[min(h, 8)]
        return graph


# ─── Famous Patterns ───

PATTERNS = {
    "glider": [
        " # ",
        "  #",
        "###",
    ],
    "blinker": [
        "###",
    ],
    "toad": [
        " ###",
        "### ",
    ],
    "beacon": [
        "##  ",
        "#   ",
        "   #",
        "  ##",
    ],
    "r_pentomino": [
        " ##",
        "## ",
        " # ",
    ],
    "glider_gun": [
        "                        #             ",
        "                      # #             ",
        "            ##      ##            ##  ",
        "           #   #    ##            ##  ",
        "##        #     #   ##                ",
        "##        #   # ##    # #             ",
        "          #     #       #             ",
        "           #   #                      ",
        "            ##                        ",
    ],
    "acorn": [
        " #     ",
        "   #   ",
        "##  ###",
    ],
    "diehard": [
        "      # ",
        "##      ",
        " #   ###",
    ],
}


def run_demo(pattern_name="r_pentomino", generations=200, delay=0.08):
    """Run a visual demo of a pattern."""
    game = GameOfLife(60, 30)
    
    if pattern_name not in PATTERNS:
        print(f"Unknown pattern: {pattern_name}")
        print(f"Available: {', '.join(PATTERNS.keys())}")
        return
    
    # Center the pattern
    pattern = PATTERNS[pattern_name]
    pw = max(len(row) for row in pattern)
    ph = len(pattern)
    ox = (game.width - pw) // 2
    oy = (game.height - ph) // 2
    game.add_pattern(pattern, ox, oy)
    
    print(f"\n═══ Conway's Game of Life: {pattern_name} ═══\n")
    
    for _ in range(generations):
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        print(game.render())
        print(game.population_graph())
        
        result = game.step()
        if result:
            print(f"\n✦ {result}")
            break
        
        time.sleep(delay)
    
    print(f"\nFinal: gen {game.generation}, pop {len(game.cells)}")
    if game.history:
        print(f"Peak population: {max(game.history)}")
        print(f"Min population: {min(game.history)}")


def run_snapshot(pattern_name="r_pentomino", generations=100, show_every=10):
    """Non-animated version — shows snapshots at intervals."""
    game = GameOfLife(60, 30)
    
    if pattern_name not in PATTERNS:
        print(f"Unknown pattern: {pattern_name}")
        print(f"Available: {', '.join(PATTERNS.keys())}")
        return
    
    pattern = PATTERNS[pattern_name]
    pw = max(len(row) for row in pattern)
    ph = len(pattern)
    ox = (game.width - pw) // 2
    oy = (game.height - ph) // 2
    game.add_pattern(pattern, ox, oy)
    
    print(f"\n═══ Conway's Game of Life: {pattern_name} ═══")
    print(f"Running {generations} generations, showing every {show_every}\n")
    
    # Show initial state
    print(game.render())
    print()
    
    for i in range(generations):
        result = game.step()
        if result:
            print(game.render())
            print(f"\n✦ {result}")
            break
        if (i + 1) % show_every == 0:
            print(game.render())
            print(game.population_graph())
            print()
    
    print(f"Final: gen {game.generation}, pop {len(game.cells)}")
    if game.history:
        print(f"Peak population: {max(game.history)}")


if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "r_pentomino"
    mode = sys.argv[2] if len(sys.argv) > 2 else "snapshot"
    
    if mode == "animate":
        run_demo(pattern)
    else:
        run_snapshot(pattern, generations=100, show_every=25)