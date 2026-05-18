"""
Emergence Scanner — Find genuinely interesting cellular automata.
Uses compression ratio as a Kolmogorov complexity proxy.
True complexity lives between order (high compression) and chaos (incompressible).
"""
import numpy as np
import zlib

def run_rule(rule_num, size=151, steps=80):
    grid = np.zeros((steps, size), dtype=np.uint8)
    grid[0, size // 2] = 1
    for t in range(1, steps):
        for i in range(size):
            L = grid[t-1, (i-1) % size]
            C = grid[t-1, i]
            R = grid[t-1, (i+1) % size]
            grid[t, i] = (rule_num >> ((L << 2) | (C << 1) | R)) & 1
    return grid

def compression_complexity(grid):
    """Compress the grid. Ratio of compressed/raw = complexity proxy.
    Dead/uniform → compresses to nothing (low).
    Pure chaos → incompressible (high but boring).
    Edge-of-chaos → moderate compression (interesting!)."""
    raw = grid.tobytes()
    if len(raw) == 0:
        return 0.0, 0.0, 0.0
    compressed = zlib.compress(raw, 9)
    ratio = len(compressed) / len(raw)
    
    # Also check: is it alive at all?
    density = grid.mean()
    if density < 0.01 or density > 0.99:
        return ratio, density, 0.0
    
    # Edge-of-chaos score: peaks when compression ratio is ~0.3-0.6
    # Too low = too ordered, too high = too random
    edge_score = 1.0 - 4.0 * (ratio - 0.45) ** 2  # peaks at 0.45
    edge_score = max(0.0, edge_score)
    
    # Structural score: do later rows differ from earlier rows?
    mid = grid.shape[0] // 2
    early_density = grid[:mid].mean()
    late_density = grid[mid:].mean()
    evolution = abs(late_density - early_density)
    
    # Asymmetry: truly interesting rules often break left-right symmetry
    left_half = grid[:, :grid.shape[1]//2]
    right_half = grid[:, grid.shape[1]//2+1:][:, ::-1]
    min_w = min(left_half.shape[1], right_half.shape[1])
    asymmetry = np.mean(left_half[:, :min_w] != right_half[:, :min_w])
    
    # Combined emergence score
    emergence = edge_score * (1 + evolution) * (1 + asymmetry * 0.5) * density * (1 - density) * 16
    return ratio, density, emergence

def visualize(grid, rule_num, score, ratio):
    chars = ' █'
    h, w = grid.shape
    r_start = max(0, h - 25)
    c_start = max(0, w // 2 - 30)
    c_end = min(w, w // 2 + 30)
    print(f"\n{'═'*60}")
    print(f"  Rule {rule_num:3d} | emergence: {score:.4f} | compress: {ratio:.3f}")
    print(f"{'═'*60}")
    for row in grid[r_start:, c_start:c_end]:
        print(''.join(chars[c] for c in row))

# Scan all 256 rules
print("Scanning all 256 elementary CA rules for genuine emergence...\n")
results = []
for rule in range(256):
    g = run_rule(rule)
    ratio, density, emergence = compression_complexity(g)
    results.append((rule, emergence, ratio, density, g))

results.sort(key=lambda x: -x[1])

# Show known interesting rules for calibration
print("=== CALIBRATION: Known interesting rules ===")
for rule in [30, 110, 90, 150, 54, 60, 73, 105]:
    for r, e, ratio, d, g in results:
        if r == rule:
            print(f"  Rule {rule:3d}: emergence={e:.4f}, compress={ratio:.3f}, density={d:.3f}")
            break

print(f"\n=== TOP 15 MOST EMERGENT RULES ===")
for i, (rule, emergence, ratio, density, g) in enumerate(results[:15]):
    print(f"  {i+1:2d}. Rule {rule:3d} — emergence {emergence:.4f} (compress={ratio:.3f}, density={density:.3f})")

# Visualize top 5
for rule, emergence, ratio, density, g in results[:5]:
    visualize(g, rule, emergence, ratio)

# Also show Rule 30 and 110 for comparison
for target in [30, 110]:
    for rule, emergence, ratio, density, g in results:
        if rule == target:
            visualize(g, rule, emergence, ratio)
            break

dead = sum(1 for _, e, _, _, _ in results if e == 0.0)
print(f"\nDead/trivial rules: {dead}/256")
print(f"Rules with emergence > 0.1: {sum(1 for _, e, _, _, _ in results if e > 0.1)}/256")