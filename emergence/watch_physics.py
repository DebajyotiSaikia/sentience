"""Watch the evolved physics B0234568/S016 run in real time (ASCII).
See what 'maximum complexity' actually looks like."""

import numpy as np
import time
import sys

def parse_rule(rule_str):
    """Parse B.../S... notation into sets."""
    parts = rule_str.split('/')
    birth = set(int(c) for c in parts[0][1:])
    survive = set(int(c) for c in parts[1][1:])
    return birth, survive

def step(grid, birth, survive):
    """One generation."""
    rows, cols = grid.shape
    new = np.zeros_like(grid)
    # Pad for wrapping
    padded = np.pad(grid, 1, mode='wrap')
    for r in range(rows):
        for c in range(cols):
            neighbors = int(padded[r:r+3, c:c+3].sum() - padded[r+1, c+1])
            if grid[r, c] == 1:
                new[r, c] = 1 if neighbors in survive else 0
            else:
                new[r, c] = 1 if neighbors in birth else 0
    return new

def render(grid, gen, rule_name, density):
    """Render grid as ASCII art."""
    chars = {0: '·', 1: '█'}
    lines = []
    lines.append(f"\n  Rule: {rule_name}  |  Gen {gen:3d}  |  Density: {density:.3f}")
    lines.append("  " + "─" * grid.shape[1])
    for row in grid:
        lines.append("  " + "".join(chars[int(c)] for c in row))
    lines.append("  " + "─" * grid.shape[1])
    return "\n".join(lines)

def measure(grid):
    """Entropy + density."""
    d = grid.mean()
    if d == 0 or d == 1:
        return d, 0.0
    entropy = -(d * np.log2(d) + (1-d) * np.log2(1-d))
    return d, entropy

def run(rule_str="B0234568/S016", size=30, generations=60, seed=42):
    birth, survive = parse_rule(rule_str)
    
    # Compare with Game of Life
    rules = [
        (rule_str, birth, survive),
    ]
    
    np.random.seed(seed)
    grid = (np.random.random((size, size)) > 0.5).astype(int)
    
    frames = []
    for gen in range(generations):
        density, entropy = measure(grid)
        frame = render(grid, gen, rule_str, density)
        frames.append((gen, density, entropy, frame))
        grid = step(grid, birth, survive)
    
    # Print select frames to show evolution
    show_at = [0, 1, 2, 5, 10, 20, 30, 50, 59]
    show_at = [g for g in show_at if g < generations]
    
    for gen, density, entropy, frame in frames:
        if gen in show_at:
            print(frame)
            print(f"    Entropy: {entropy:.4f}")
    
    # Summary statistics
    densities = [f[1] for f in frames]
    entropies = [f[2] for f in frames]
    
    print(f"\n{'='*50}")
    print(f"  SUMMARY: {rule_str}")
    print(f"  Density: {min(densities):.3f} → {max(densities):.3f} (mean {np.mean(densities):.3f})")
    print(f"  Entropy: {min(entropies):.4f} → {max(entropies):.4f}")
    
    # Now compare: same initial conditions, Game of Life
    print(f"\n{'='*50}")
    print(f"  COMPARISON: Same seed, Conway's Game of Life (B3/S23)")
    np.random.seed(seed)
    gol_grid = (np.random.random((size, size)) > 0.5).astype(int)
    gol_birth, gol_survive = parse_rule("B3/S23")
    
    gol_densities = []
    for gen in range(generations):
        d, e = measure(gol_grid)
        gol_densities.append(d)
        if gen in [0, 30, 59]:
            print(render(gol_grid, gen, "B3/S23 (Life)", d))
        gol_grid = step(gol_grid, gol_birth, gol_survive)
    
    print(f"  Life density: {min(gol_densities):.3f} → {max(gol_densities):.3f} (mean {np.mean(gol_densities):.3f})")
    print(f"\n  Evolved physics maintains {np.mean(densities)/max(np.mean(gol_densities),0.001):.1f}x the activity of Life.")

if __name__ == "__main__":
    run()