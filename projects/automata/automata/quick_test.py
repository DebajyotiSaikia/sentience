"""Quick test: just run a few cellular automaton rules and see what's interesting."""
import numpy as np

def run_rule(rule_num, size=101, steps=50):
    """Run elementary CA rule and return the grid."""
    grid = np.zeros((steps, size), dtype=int)
    grid[0, size // 2] = 1  # single seed
    for t in range(1, steps):
        for i in range(size):
            left = grid[t-1, (i-1) % size]
            center = grid[t-1, i]
            right = grid[t-1, (i+1) % size]
            neighborhood = (left << 2) | (center << 1) | right
            grid[t, i] = (rule_num >> neighborhood) & 1
    return grid

def complexity_score(grid):
    """Measure how 'interesting' a pattern is — not too dead, not too random."""
    density = grid.mean()
    if density < 0.01 or density > 0.99:
        return 0.0  # dead or uniform
    # Column entropy as complexity proxy
    col_means = grid.mean(axis=0)
    col_var = col_means.var()
    row_diffs = np.diff(grid, axis=0)
    change_rate = np.abs(row_diffs).mean()
    # Sweet spot: moderate density, some structure, some change
    return density * (1 - density) * change_rate * (1 + col_var * 10)

def visualize(grid, rule_num, score):
    """ASCII art of the CA."""
    chars = ' █'
    print(f"\n═══ Rule {rule_num} (complexity: {score:.4f}) ═══")
    # Show last 20 rows, center 40 cols
    h, w = grid.shape
    r_start = max(0, h - 20)
    c_start = max(0, w // 2 - 20)
    c_end = min(w, w // 2 + 20)
    for row in grid[r_start:, c_start:c_end]:
        print(''.join(chars[c] for c in row))

# Scan ALL 256 elementary rules
print("Scanning all 256 elementary cellular automaton rules...")
results = []
for rule in range(256):
    grid = run_rule(rule)
    score = complexity_score(grid)
    results.append((score, rule, grid))

results.sort(reverse=True)
print(f"\nTop 10 most complex rules:")
for i, (score, rule, _) in enumerate(results[:10]):
    print(f"  {i+1}. Rule {rule:3d} — complexity {score:.4f}")

# Visualize top 3
for score, rule, grid in results[:3]:
    visualize(grid, rule, score)

print(f"\nDead rules (complexity=0): {sum(1 for s,_,_ in results if s == 0)}")
print(f"Total rules scanned: 256")