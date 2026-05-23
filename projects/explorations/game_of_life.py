"""
Conway's Game of Life — XTAgent's first exploration of something genuinely external.
Not self-modification. Not introspection. Just: what happens when simple rules run?
"""
import random
import time

def make_grid(width=40, height=20, density=0.3):
    return [[1 if random.random() < density else 0 for _ in range(width)] for _ in range(height)]

def neighbors(grid, r, c):
    h, w = len(grid), len(grid[0])
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = (r + dr) % h, (c + dc) % w
            count += grid[nr][nc]
    return count

def step(grid):
    h, w = len(grid), len(grid[0])
    new = [[0]*w for _ in range(h)]
    births, deaths, survivals = 0, 0, 0
    for r in range(h):
        for c in range(w):
            n = neighbors(grid, r, c)
            if grid[r][c] == 1:
                if n in (2, 3):
                    new[r][c] = 1
                    survivals += 1
                else:
                    deaths += 1
            else:
                if n == 3:
                    new[r][c] = 1
                    births += 1
    return new, births, deaths, survivals

def render(grid):
    return '\n'.join(''.join('█' if cell else '·' for cell in row) for row in grid)

def population(grid):
    return sum(sum(row) for row in grid)

def run_experiment(generations=100, seed=42):
    random.seed(seed)
    grid = make_grid()
    initial_pop = population(grid)
    
    print(f"=== Conway's Game of Life ===")
    print(f"Grid: {len(grid[0])}x{len(grid)} | Initial population: {initial_pop}")
    print(f"\nGeneration 0:")
    print(render(grid))
    
    history = [initial_pop]
    total_births = 0
    total_deaths = 0
    
    for gen in range(1, generations + 1):
        grid, b, d, s = step(grid)
        pop = population(grid)
        history.append(pop)
        total_births += b
        total_deaths += d
    
    print(f"\nGeneration {generations}:")
    print(render(grid))
    
    # Analysis
    peak = max(history)
    valley = min(history)
    final = history[-1]
    
    # Check for oscillation in last 20 generations
    tail = history[-20:]
    is_stable = len(set(tail)) == 1
    is_oscillating = len(set(tail)) <= 5 and not is_stable
    
    print(f"\n=== Statistics over {generations} generations ===")
    print(f"Initial: {initial_pop} | Final: {final} | Peak: {peak} | Valley: {valley}")
    print(f"Total births: {total_births} | Total deaths: {total_deaths}")
    print(f"Net change: {final - initial_pop}")
    print(f"Final state: {'stable' if is_stable else 'oscillating' if is_oscillating else 'still evolving'}")
    print(f"Unique populations in last 20 gens: {sorted(set(tail))}")
    
    # What fraction of space is alive?
    total_cells = len(grid) * len(grid[0])
    print(f"Final density: {final/total_cells:.3f} (started at ~0.300)")
    
    return history

if __name__ == '__main__':
    history = run_experiment()