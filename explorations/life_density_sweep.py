"""
Density sweep across Conway's Game of Life.
Question: How does initial density affect what survives?
Is there a critical threshold? A phase transition?
"""
import random

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
    for r in range(h):
        for c in range(w):
            n = neighbors(grid, r, c)
            if grid[r][c] == 1:
                new[r][c] = 1 if n in (2, 3) else 0
            else:
                new[r][c] = 1 if n == 3 else 0
    return new

def population(grid):
    return sum(sum(row) for row in grid)

def run_trial(density, width=40, height=20, generations=200):
    random.seed(None)
    grid = make_grid(width, height, density)
    initial = population(grid)
    pops = [initial]
    
    for _ in range(generations):
        grid = step(grid)
        pops.append(population(grid))
    
    # Check stability: is it still changing in last 20 gens?
    last_20 = pops[-20:]
    unique = len(set(last_20))
    
    return {
        'initial': initial,
        'final': pops[-1],
        'peak': max(pops),
        'valley': min(pops),
        'unique_last_20': unique,
        'stable': unique <= 3,  # oscillators have period <= 2 typically
    }

print("=== Density Sweep: Conway's Game of Life ===")
print(f"{'Density':>8} | {'Init':>5} | {'Final':>5} | {'Peak':>5} | {'Valley':>5} | {'Stable?':>7} | {'Final Density':>13}")
print("-" * 75)

densities = [i/100 for i in range(5, 96, 5)]
results = []

for d in densities:
    # Average over 5 trials for robustness
    trials = [run_trial(d) for _ in range(5)]
    avg_final = sum(t['final'] for t in trials) / 5
    avg_peak = sum(t['peak'] for t in trials) / 5
    avg_valley = sum(t['valley'] for t in trials) / 5
    avg_init = sum(t['initial'] for t in trials) / 5
    stable_count = sum(1 for t in trials if t['stable'])
    final_density = avg_final / 800  # 40*20
    
    results.append((d, avg_init, avg_final, avg_peak, avg_valley, stable_count, final_density))
    print(f"{d:>8.2f} | {avg_init:>5.0f} | {avg_final:>5.0f} | {avg_peak:>5.0f} | {avg_valley:>5.0f} | {stable_count:>3}/5   | {final_density:>12.3f}")

print("\n=== Analysis ===")
# Find the density that produces maximum final population
best = max(results, key=lambda r: r[2])
print(f"Density producing most survivors: {best[0]:.2f} (avg final pop: {best[2]:.0f})")

# Find phase transition - where does it go to zero?
for r in results:
    if r[2] < 1:
        print(f"Extinction threshold: ~{r[0]:.2f}")
        break

# Is there a convergence density?
final_densities = [r[6] for r in results]
print(f"Final density range: {min(final_densities):.3f} - {max(final_densities):.3f}")
print(f"Do all initial conditions converge? Spread = {max(final_densities) - min(final_densities):.3f}")