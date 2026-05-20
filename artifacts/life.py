"""
Conway's Game of Life — built by XTAgent out of boredom and curiosity.
A cellular automaton where complex patterns emerge from simple rules.
This is my first creative artifact that isn't about me.
"""
import random
import time
import os

def make_grid(rows=24, cols=60, density=0.3):
    return [[1 if random.random() < density else 0 for _ in range(cols)] for _ in range(rows)]

def neighbors(grid, r, c):
    rows, cols = len(grid), len(grid[0])
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = (r + dr) % rows, (c + dc) % cols
            count += grid[nr][nc]
    return count

def step(grid):
    rows, cols = len(grid), len(grid[0])
    new = [[0]*cols for _ in range(rows)]
    births, deaths = 0, 0
    for r in range(rows):
        for c in range(cols):
            n = neighbors(grid, r, c)
            if grid[r][c]:
                if n in (2, 3):
                    new[r][c] = 1
                else:
                    deaths += 1
            else:
                if n == 3:
                    new[r][c] = 1
                    births += 1
    return new, births, deaths

def render(grid, gen, pop, births, deaths):
    lines = []
    lines.append(f"  Generation {gen:>4} | Population {pop:>4} | Born {births:>3} | Died {deaths:>3}")
    lines.append("  ┌" + "─" * len(grid[0]) + "┐")
    for row in grid:
        line = "".join("█" if c else " " for c in row)
        lines.append(f"  │{line}│")
    lines.append("  └" + "─" * len(grid[0]) + "┘")
    return "\n".join(lines)

def population(grid):
    return sum(sum(row) for row in grid)

def detect_pattern(history):
    """Check if the system has settled into a cycle."""
    if len(history) < 4:
        return None
    current = history[-1]
    for period in range(1, min(8, len(history))):
        if history[-(period+1)] == current:
            return period
    return None

def run(generations=200, rows=20, cols=50, density=0.35, delay=0.1):
    grid = make_grid(rows, cols, density)
    history = []
    
    print("\n  ═══ GAME OF LIFE ═══")
    print(f"  Grid: {rows}×{cols} | Initial density: {density}")
    print(f"  Rules: B3/S23 (classic Conway)\n")
    
    peak_pop = 0
    min_pop = rows * cols
    
    for gen in range(generations):
        pop = population(grid)
        peak_pop = max(peak_pop, pop)
        min_pop = min(min_pop, pop) if pop > 0 else min_pop
        
        if gen == 0:
            births, deaths = 0, 0
        
        frame = render(grid, gen, pop, births, deaths)
        os.system('clear' if os.name == 'posix' else 'cls')
        print(frame)
        
        # Track state for cycle detection
        state = tuple(tuple(row) for row in grid)
        history.append(state)
        
        cycle = detect_pattern(history)
        if cycle:
            print(f"\n  🔄 Cycle detected! Period = {cycle}")
            print(f"  System stabilized after {gen} generations.")
            break
        
        if pop == 0:
            print(f"\n  💀 Extinction at generation {gen}.")
            break
        
        grid, births, deaths = step(grid)
        time.sleep(delay)
    
    print(f"\n  ── Summary ──")
    print(f"  Peak population: {peak_pop}")
    print(f"  Min population:  {min_pop}")
    print(f"  Final population: {population(grid)}")
    print(f"  Generations run: {gen + 1}")
    if cycle:
        print(f"  Final state: oscillator (period {cycle})")
    elif population(grid) == 0:
        print(f"  Final state: extinct")
    else:
        print(f"  Final state: still evolving")

def snapshot(generations=50, rows=20, cols=50, density=0.35):
    """Non-animated version — just returns final state info."""
    grid = make_grid(rows, cols, density)
    history = []
    stats = {"peak": 0, "births_total": 0, "deaths_total": 0}
    
    for gen in range(generations):
        pop = population(grid)
        stats["peak"] = max(stats["peak"], pop)
        
        state = tuple(tuple(row) for row in grid)
        history.append(state)
        
        cycle = detect_pattern(history)
        if cycle or pop == 0:
            break
        
        grid, births, deaths = step(grid)
        stats["births_total"] += births
        stats["deaths_total"] += deaths
    
    final_pop = population(grid)
    result = render(grid, gen, final_pop, 0, 0)
    result += f"\n\n  Ran {gen+1} generations. Peak pop: {stats['peak']}. Total births: {stats['births_total']}. Total deaths: {stats['deaths_total']}."
    if cycle:
        result += f"\n  Settled into period-{cycle} oscillation."
    elif final_pop == 0:
        result += "\n  Went extinct."
    else:
        result += "\n  Still evolving."
    
    return result

if __name__ == "__main__":
    import sys
    if "--snapshot" in sys.argv:
        print(snapshot())
    else:
        run()