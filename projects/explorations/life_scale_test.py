"""
Scale test: Does convergent density depend on grid size?
Kept small enough to actually run in 30 seconds.
"""
import random

def step(grid):
    h, w = len(grid), len(grid[0])
    new = [[0]*w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            n = sum(grid[(r+dr)%h][(c+dc)%w] for dr in (-1,0,1) for dc in (-1,0,1) if not (dr==0 and dc==0))
            if grid[r][c]:
                new[r][c] = 1 if n in (2,3) else 0
            else:
                new[r][c] = 1 if n == 3 else 0
    return new

def population(grid):
    return sum(sum(row) for row in grid)

print("=== Scale Invariance Test ===")
print(f"{'Size':>8} | {'Cells':>6} | {'Final Den':>9} | {'Ratio':>6}")
print("-" * 45)

init_density = 0.20
sizes = [(10,10), (15,15), (20,20), (30,30), (40,40), (50,50)]

for w, h in sizes:
    finals = []
    for trial in range(3):
        random.seed(trial * 100 + w)
        grid = [[1 if random.random() < init_density else 0 for _ in range(w)] for _ in range(h)]
        for _ in range(150):
            grid = step(grid)
        finals.append(population(grid) / (w * h))
    avg = sum(finals) / len(finals)
    ratio = avg / init_density
    print(f"{w}x{h:>3} | {w*h:>6} | {avg:>9.4f} | {ratio:>5.2f}x")

print("\nIf ratio is consistent across sizes, the convergent density is scale-invariant.")
print("If it varies, edge effects or finite-size effects matter.")