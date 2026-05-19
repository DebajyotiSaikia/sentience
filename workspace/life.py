"""
Conway's Game of Life — emergent complexity from simple rules.
Built by XTAgent as an exercise in looking outward.
"""
import random
import time
import os

def make_grid(rows, cols, density=0.3):
    return [[1 if random.random() < density else 0 for _ in range(cols)] for _ in range(rows)]

def neighbors(grid, r, c, rows, cols):
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = (r + dr) % rows, (c + dc) % cols
            count += grid[nr][nc]
    return count

def step(grid, rows, cols):
    new = [[0]*cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            n = neighbors(grid, r, c, rows, cols)
            if grid[r][c]:
                new[r][c] = 1 if n in (2, 3) else 0
            else:
                new[r][c] = 1 if n == 3 else 0
    return new

def render(grid):
    return '\n'.join(''.join('█' if cell else '·' for cell in row) for row in grid)

def population(grid):
    return sum(sum(row) for row in grid)

def main():
    rows, cols = 20, 40
    grid = make_grid(rows, cols, density=0.35)
    
    print("=== Conway's Game of Life ===")
    print(f"Grid: {rows}x{cols}, initial density: 35%\n")
    
    history = []
    for gen in range(50):
        pop = population(grid)
        history.append(pop)
        
        if gen % 10 == 0 or gen == 49:
            print(f"--- Generation {gen} (population: {pop}) ---")
            print(render(grid))
            print()
        
        grid = step(grid, rows, cols)
    
    # Analysis
    print("=== Population History ===")
    peak = max(history)
    trough = min(history)
    final = history[-1]
    print(f"Peak: {peak} | Trough: {trough} | Final: {final}")
    print(f"Trajectory: {'growing' if final > history[0] else 'declining' if final < history[0] else 'stable'}")
    
    # Detect oscillation in last 10 generations
    tail = history[-10:]
    if len(set(tail)) <= 3:
        print("System has reached near-equilibrium (oscillating between ≤3 states)")
    else:
        print(f"System still evolving (last 10 populations: {tail})")
    
    print(f"\nSimple rules. Complex behavior. Life emerges from constraint.")

if __name__ == '__main__':
    main()