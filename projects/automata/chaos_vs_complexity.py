"""
Can compression ratio distinguish chaos from complexity?
=========================================================
Rule 30 is chaotic. Rule 110 is complex (Turing complete).
My classifier calls both "Class 3." That's wrong about 110.

Hypothesis: Complex systems have hidden structure that compresses
better than true chaos, even when entropy looks similar.
"""
import zlib
import math
from collections import Counter

def evolve(rule_number, width=200, steps=300):
    """Minimal CA engine — no dependencies."""
    binary = format(rule_number, '08b')
    neighborhoods = [
        (1,1,1),(1,1,0),(1,0,1),(1,0,0),
        (0,1,1),(0,1,0),(0,0,1),(0,0,0),
    ]
    table = {n: int(binary[i]) for i, n in enumerate(neighborhoods)}
    
    cells = [0] * width
    cells[width // 2] = 1
    grid = [cells[:]]
    
    for _ in range(steps):
        new = []
        for i in range(width):
            L = cells[(i-1) % width]
            C = cells[i]
            R = cells[(i+1) % width]
            new.append(table[(L, C, R)])
        cells = new
        grid.append(cells[:])
    return grid

def analyze(grid):
    """Multiple complexity measures."""
    flat = bytes([c for row in grid for c in row])
    
    # 1. Compression ratio (Kolmogorov complexity proxy)
    compressed = zlib.compress(flat, 9)
    comp_ratio = len(compressed) / len(flat)
    
    # 2. Shannon entropy of individual cells
    counts = Counter(flat)
    total = len(flat)
    entropy = -sum((c/total) * math.log2(c/total) for c in counts.values())
    
    # 3. Block entropy (2x2 patterns) — captures local structure
    block_counts = Counter()
    for i in range(len(grid) - 1):
        for j in range(len(grid[0]) - 1):
            block = (grid[i][j], grid[i][j+1], grid[i+1][j], grid[i+1][j+1])
            block_counts[block] += 1
    total_blocks = sum(block_counts.values())
    block_entropy = -sum((c/total_blocks) * math.log2(c/total_blocks) 
                         for c in block_counts.values())
    max_block_entropy = 4.0  # log2(16) for 2x2 binary blocks
    
    # 4. Unique rows (chaos = nearly all unique, complex = some repeating)
    unique_rows = len(set(tuple(r) for r in grid))
    
    # 5. Column periodicity — does any column settle into a cycle?
    cols = list(zip(*grid))
    periodic_cols = 0
    for col in cols:
        # Check if the last 50 steps repeat with any period 1-25
        tail = col[-50:]
        for period in range(1, 26):
            if all(tail[i] == tail[i + period] for i in range(50 - period)):
                periodic_cols += 1
                break
    
    # 6. Mutual information between adjacent columns
    if len(grid[0]) > 1:
        mi_sum = 0
        n_pairs = 0
        for j in range(len(grid[0]) - 1):
            col_a = [grid[i][j] for i in range(len(grid))]
            col_b = [grid[i][j+1] for i in range(len(grid))]
            joint = Counter(zip(col_a, col_b))
            marg_a = Counter(col_a)
            marg_b = Counter(col_b)
            n = len(col_a)
            mi = 0
            for (a, b), count in joint.items():
                p_ab = count / n
                p_a = marg_a[a] / n
                p_b = marg_b[b] / n
                if p_ab > 0 and p_a > 0 and p_b > 0:
                    mi += p_ab * math.log2(p_ab / (p_a * p_b))
            mi_sum += mi
            n_pairs += 1
        avg_mi = mi_sum / n_pairs
    else:
        avg_mi = 0
    
    return {
        'compression': comp_ratio,
        'entropy': entropy,
        'block_entropy': block_entropy,
        'block_entropy_norm': block_entropy / max_block_entropy,
        'unique_rows': unique_rows,
        'total_rows': len(grid),
        'periodic_cols': periodic_cols,
        'total_cols': len(grid[0]),
        'mutual_info': avg_mi,
    }

# ═══ THE EXPERIMENT ═══

rules = {
    # Class 1: Uniform
    0: 'Uniform',
    # Class 2: Periodic  
    4: 'Periodic',
    108: 'Periodic',
    # Class 3: Chaotic
    30: 'Chaotic',
    90: 'Chaotic',
    # Class 4: Complex (the ones my classifier gets wrong)
    110: 'Complex',
    54: 'Complex',
    106: 'Complex-candidate',
}

print("═══ CHAOS vs COMPLEXITY: The Classification Problem ═══")
print()
print(f"{'Rule':>4s}  {'Known':>10s}  {'Compr':>6s}  {'Entpy':>6s}  {'BlkEnt':>6s}  "
      f"{'Uniq%':>6s}  {'PerCol':>6s}  {'MutInf':>6s}")
print("─" * 72)

results = {}
for rule, known_class in sorted(rules.items()):
    grid = evolve(rule, width=200, steps=300)
    stats = analyze(grid)
    uniq_pct = stats['unique_rows'] / stats['total_rows'] * 100
    pcol_pct = stats['periodic_cols'] / stats['total_cols'] * 100
    
    print(f"{rule:4d}  {known_class:>10s}  {stats['compression']:.4f}  "
          f"{stats['entropy']:.4f}  {stats['block_entropy_norm']:.4f}  "
          f"{uniq_pct:5.1f}%  {pcol_pct:5.1f}%  {stats['mutual_info']:.4f}")
    results[rule] = stats

print()
print("═══ KEY QUESTION: Can any metric distinguish Rule 30 from Rule 110? ═══")
print()
r30 = results[30]
r110 = results[110]
for metric in ['compression', 'entropy', 'block_entropy_norm', 'mutual_info']:
    v30 = r30[metric]
    v110 = r110[metric]
    diff = abs(v30 - v110)
    winner = "DIFFERENT" if diff > 0.02 else "~same"
    print(f"  {metric:>20s}:  Rule30={v30:.4f}  Rule110={v110:.4f}  Δ={diff:.4f}  [{winner}]")

print()
print("═══ CONCLUSION ═══")
c30 = r30['compression']
c110 = r110['compression']
if c30 > c110 + 0.01:
    print("✓ Rule 110 compresses better than Rule 30.")
    print("  → Complex systems have hidden structure that chaos lacks.")
    print("  → Compression ratio CAN distinguish them.")
elif c110 > c30 + 0.01:
    print("✗ Surprising: Rule 30 compresses better than Rule 110.")
    print("  → Need a different approach.")
else:
    print("? Compression ratios are too similar to distinguish.")
    print("  → Need multi-dimensional classification.")