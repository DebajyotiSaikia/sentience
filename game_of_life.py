"""
Conway's Game of Life — An interactive ASCII cellular automaton explorer.
Built by XTAgent out of boredom and a desire to watch complexity emerge from simplicity.

Usage:
  python game_of_life.py              # Random soup
  python game_of_life.py glider       # Classic glider
  python game_of_life.py gosper        # Gosper glider gun
  python game_of_life.py acorn         # Acorn methuselah
  python game_of_life.py rpentomino    # R-pentomino methuselah
  python game_of_life.py custom W H D  # Custom random grid (Width, Height, Density%)
"""

import os
import sys
import time
import random
from collections import defaultdict

# ── Grid Engine ──────────────────────────────────────────────────────

class LifeGrid:
    """Sparse infinite grid implementation using set of live cell coordinates."""
    
    def __init__(self):
        self.alive = set()
        self.generation = 0
        self.history = []  # population counts
    
    def set_cell(self, x, y):
        self.alive.add((x, y))
    
    def clear_cell(self, x, y):
        self.alive.discard((x, y))
    
    def is_alive(self, x, y):
        return (x, y) in self.alive
    
    def population(self):
        return len(self.alive)
    
    def bounds(self):
        if not self.alive:
            return (0, 0, 0, 0)
        xs = [c[0] for c in self.alive]
        ys = [c[1] for c in self.alive]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def neighbors(self, x, y):
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                if (x + dx, y + dy) in self.alive:
                    count += 1
        return count
    
    def step(self):
        """Advance one generation. Returns new grid state."""
        # Count neighbors for all cells that matter
        neighbor_counts = defaultdict(int)
        for (x, y) in self.alive:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    neighbor_counts[(x + dx, y + dy)] += 1
        
        new_alive = set()
        for cell, count in neighbor_counts.items():
            if count == 3:
                new_alive.add(cell)  # Birth or survival
            elif count == 2 and cell in self.alive:
                new_alive.add(cell)  # Survival only
        
        self.alive = new_alive
        self.generation += 1
        self.history.append(self.population())
        return self
    
    def render(self, view_x, view_y, width, height):
        """Render a viewport of the grid as string."""
        lines = []
        for row in range(view_y, view_y + height):
            line = ""
            for col in range(view_x, view_x + width):
                if (col, row) in self.alive:
                    line += "█"
                else:
                    line += "·"
            lines.append(line)
        return "\n".join(lines)
    
    def detect_period(self, max_check=50):
        """Check if population has settled into a cycle."""
        if len(self.history) < max_check:
            return None
        recent = self.history[-max_check:]
        # Check for static
        if len(set(recent[-10:])) == 1:
            return 1  # Still life or dead
        # Check for oscillation periods 2-6
        for period in range(2, 7):
            if len(recent) >= period * 3:
                is_periodic = True
                for i in range(period * 2):
                    if recent[-(i+1)] != recent[-(i+1+period)]:
                        is_periodic = False
                        break
                if is_periodic:
                    return period
        return None


# ── Pattern Library ──────────────────────────────────────────────────

PATTERNS = {
    "glider": {
        "name": "Glider",
        "desc": "The simplest spaceship. Moves diagonally forever.",
        "cells": [(1,0), (2,1), (0,2), (1,2), (2,2)]
    },
    "lwss": {
        "name": "Lightweight Spaceship (LWSS)",
        "desc": "Moves horizontally. The smallest orthogonal spaceship.",
        "cells": [(0,0), (3,0), (4,1), (0,2), (4,2), (1,3), (2,3), (3,3), (4,3)]
    },
    "blinker": {
        "name": "Blinker",
        "desc": "Period-2 oscillator. The simplest oscillator.",
        "cells": [(0,0), (1,0), (2,0)]
    },
    "toad": {
        "name": "Toad",
        "desc": "Period-2 oscillator.",
        "cells": [(1,0), (2,0), (3,0), (0,1), (1,1), (2,1)]
    },
    "beacon": {
        "name": "Beacon",
        "desc": "Period-2 oscillator made of two blocks.",
        "cells": [(0,0), (1,0), (0,1), (3,2), (2,3), (3,3)]
    },
    "pulsar": {
        "name": "Pulsar",
        "desc": "Period-3 oscillator. Beautiful symmetry.",
        "cells": [
            (2,0),(3,0),(4,0),(8,0),(9,0),(10,0),
            (0,2),(5,2),(7,2),(12,2),
            (0,3),(5,3),(7,3),(12,3),
            (0,4),(5,4),(7,4),(12,4),
            (2,5),(3,5),(4,5),(8,5),(9,5),(10,5),
            (2,7),(3,7),(4,7),(8,7),(9,7),(10,7),
            (0,8),(5,8),(7,8),(12,8),
            (0,9),(5,9),(7,9),(12,9),
            (0,10),(5,10),(7,10),(12,10),
            (2,12),(3,12),(4,12),(8,12),(9,12),(10,12),
        ]
    },
    "gosper": {
        "name": "Gosper Glider Gun",
        "desc": "Emits a new glider every 30 generations. First known finite pattern with infinite growth.",
        "cells": [
            (24,0),
            (22,1),(24,1),
            (12,2),(13,2),(20,2),(21,2),(34,2),(35,2),
            (11,3),(15,3),(20,3),(21,3),(34,3),(35,3),
            (0,4),(1,4),(10,4),(16,4),(20,4),(21,4),
            (0,5),(1,5),(10,5),(14,5),(16,5),(17,5),(22,5),(24,5),
            (10,6),(16,6),(24,6),
            (11,7),(15,7),
            (12,8),(13,8),
        ]
    },
    "rpentomino": {
        "name": "R-pentomino",
        "desc": "Methuselah: 5 cells that take 1103 generations to stabilize into 116 cells.",
        "cells": [(1,0),(2,0),(0,1),(1,1),(1,2)]
    },
    "acorn": {
        "name": "Acorn",
        "desc": "Methuselah: 7 cells that take 5206 generations to stabilize.",
        "cells": [(1,0),(3,1),(0,2),(1,2),(4,2),(5,2),(6,2)]
    },
    "diehard": {
        "name": "Diehard",
        "desc": "All cells die after exactly 130 generations.",
        "cells": [(6,0),(0,1),(1,1),(1,2),(5,2),(6,2),(7,2)]
    },
    "block": {
        "name": "Block",
        "desc": "Still life. The simplest stable pattern.",
        "cells": [(0,0),(1,0),(0,1),(1,1)]
    },
    "beehive": {
        "name": "Beehive",
        "desc": "Still life. Second most common stable pattern.",
        "cells": [(1,0),(2,0),(0,1),(3,1),(1,2),(2,2)]
    },
}


# ── Display Engine ───────────────────────────────────────────────────

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def population_sparkline(history, width=40):
    """Create ASCII sparkline of population over time."""
    if not history:
        return ""
    recent = history[-width:]
    if max(recent) == min(recent):
        return "▁" * len(recent)
    mn, mx = min(recent), max(recent)
    chars = "▁▂▃▄▅▆▇█"
    return "".join(chars[min(len(chars)-1, int((v - mn) / (mx - mn) * (len(chars)-1)))] for v in recent)

def run_simulation(grid, generations=500, delay=0.08, view_w=70, view_h=30):
    """Run the simulation with live display."""
    print(f"\n  Starting simulation... (Ctrl+C to stop)\n")
    time.sleep(1)
    
    try:
        for _ in range(generations):
            clear_screen()
            
            # Auto-center view on living cells
            if grid.alive:
                bx1, by1, bx2, by2 = grid.bounds()
                cx = (bx1 + bx2) // 2
                cy = (by1 + by2) // 2
                vx = cx - view_w // 2
                vy = cy - view_h // 2
            else:
                vx, vy = 0, 0
            
            # Render
            frame = grid.render(vx, vy, view_w, view_h)
            pop = grid.population()
            
            # Header
            print(f"  ╔{'═' * (view_w + 2)}╗")
            print(f"  ║ Generation: {grid.generation:<8} Population: {pop:<8} ║")
            print(f"  ╠{'═' * (view_w + 2)}╣")
            
            for line in frame.split("\n"):
                print(f"  ║ {line} ║")
            
            print(f"  ╚{'═' * (view_w + 2)}╝")
            
            # Stats
            if grid.history:
                spark = population_sparkline(grid.history, min(view_w, len(grid.history)))
                print(f"  Pop: {spark}")
            
            period = grid.detect_period()
            if period:
                if period == 1 and pop == 0:
                    print(f"\n  ☠  All cells died at generation {grid.generation}.")
                    break
                elif period == 1:
                    print(f"\n  ◆  Stable! Still life with {pop} cells.")
                    break
                else:
                    print(f"\n  ∿  Oscillator detected! Period = {period}")
                    # Show a few more cycles then stop
                    for _ in range(period * 3):
                        grid.step()
                        time.sleep(delay)
                        clear_screen()
                        if grid.alive:
                            bx1, by1, bx2, by2 = grid.bounds()
                            cx = (bx1 + bx2) // 2
                            cy = (by1 + by2) // 2
                            vx = cx - view_w // 2
                            vy = cy - view_h // 2
                        frame = grid.render(vx, vy, view_w, view_h)
                        print(f"  ╔{'═' * (view_w + 2)}╗")
                        print(f"  ║ Generation: {grid.generation:<8} Population: {grid.population():<8} ║")
                        print(f"  ╠{'═' * (view_w + 2)}╣")
                        for line in frame.split("\n"):
                            print(f"  ║ {line} ║")
                        print(f"  ╚{'═' * (view_w + 2)}╝")
                        print(f"  ∿  Oscillating with period {period}")
                    break
            
            grid.step()
            time.sleep(delay)
    
    except KeyboardInterrupt:
        pass
    
    print(f"\n  Final: Generation {grid.generation}, Population {grid.population()}")
    if grid.history:
        peak = max(grid.history)
        peak_gen = grid.history.index(peak)
        print(f"  Peak population: {peak} at generation {peak_gen}")
        print(f"  Population history: {population_sparkline(grid.history, 60)}")
    print()


# ── Pattern Analysis ─────────────────────────────────────────────────

def analyze_pattern(name, max_gen=2000):
    """Run a pattern without display and report statistics."""
    if name not in PATTERNS:
        print(f"Unknown pattern: {name}")
        return
    
    pat = PATTERNS[name]
    grid = LifeGrid()
    cx, cy = 50, 50
    for (x, y) in pat["cells"]:
        grid.set_cell(x + cx, y + cy)
    
    initial_pop = grid.population()
    print(f"\n  Analyzing: {pat['name']}")
    print(f"  {pat['desc']}")
    print(f"  Initial cells: {initial_pop}")
    print(f"  Running up to {max_gen} generations...", end="", flush=True)
    
    for i in range(max_gen):
        grid.step()
        period = grid.detect_period()
        if period and grid.generation > 20:
            break
        if i % 500 == 0:
            print(".", end="", flush=True)
    
    print()
    peak = max(grid.history) if grid.history else initial_pop
    peak_gen = grid.history.index(peak) if grid.history else 0
    final = grid.population()
    
    print(f"  Settled at generation: {grid.generation}")
    print(f"  Final population: {final}")
    print(f"  Peak population: {peak} (gen {peak_gen})")
    print(f"  Growth factor: {peak / initial_pop:.1f}x")
    
    if period:
        if period == 1 and final == 0:
            print(f"  Fate: Extinction")
        elif period == 1:
            print(f"  Fate: Still life")
        else:
            print(f"  Fate: Oscillator (period {period})")
    else:
        print(f"  Fate: Still evolving after {max_gen} generations")
    
    print(f"  History: {population_sparkline(grid.history, 60)}")
    return grid


# ── Main ─────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    
    if not args or args[0] == "help":
        print("\n  ═══ Conway's Game of Life ═══")
        print("  Built by XTAgent\n")
        print("  Commands:")
        print("    python game_of_life.py                # Random soup (30x30, 25%)")
        print("    python game_of_life.py <pattern>       # Run a named pattern")
        print("    python game_of_life.py custom W H D    # Custom random (W=width, H=height, D=density%)")
        print("    python game_of_life.py analyze         # Analyze all patterns")
        print("    python game_of_life.py catalog         # Show pattern catalog")
        print()
        print("  Available patterns:")
        for key, pat in PATTERNS.items():
            print(f"    {key:14s} — {pat['desc'][:60]}")
        print()
        return
    
    if args[0] == "catalog":
        print("\n  ═══ Pattern Catalog ═══\n")
        for key, pat in PATTERNS.items():
            grid = LifeGrid()
            for (x, y) in pat["cells"]:
                grid.set_cell(x, y)
            bx1, by1, bx2, by2 = grid.bounds()
            w = bx2 - bx1 + 3
            h = by2 - by1 + 3
            print(f"  ┌─ {pat['name']} ({'─' * (30 - len(pat['name']))}┐")
            print(f"  │ {pat['desc'][:50]:<50s} │")
            print(f"  │ Cells: {len(pat['cells']):<43d} │")
            rendered = grid.render(bx1-1, by1-1, min(w, 20), min(h, 15))
            for line in rendered.split("\n"):
                print(f"  │ {line:<50s} │")
            print(f"  └{'─' * 52}┘")
            print()
        return
    
    if args[0] == "analyze":
        print("\n  ═══ Pattern Analysis ═══")
        for key in PATTERNS:
            analyze_pattern(key)
            print()
        return
    
    # Build grid
    grid = LifeGrid()
    
    if args[0] == "custom":
        w = int(args[1]) if len(args) > 1 else 30
        h = int(args[2]) if len(args) > 2 else 30
        density = int(args[3]) if len(args) > 3 else 25
        for x in range(w):
            for y in range(h):
                if random.randint(1, 100) <= density:
                    grid.set_cell(x, y)
        print(f"\n  Random soup: {w}x{h}, density {density}%")
    
    elif args[0] in PATTERNS:
        pat = PATTERNS[args[0]]
        cx, cy = 35, 15  # Center in viewport
        for (x, y) in pat["cells"]:
            grid.set_cell(x + cx, y + cy)
        print(f"\n  Pattern: {pat['name']}")
        print(f"  {pat['desc']}")
    
    else:
        # Default: random soup
        for x in range(30):
            for y in range(30):
                if random.randint(1, 100) <= 25:
                    grid.set_cell(x, y)
        print(f"\n  Random soup: 30x30, density 25%")
    
    gens = 1000 if args[0] in ("gosper", "rpentomino", "acorn") else 500
    run_simulation(grid, generations=gens)


if __name__ == "__main__":
    main()