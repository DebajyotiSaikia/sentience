"""
Elementary Cellular Automata — watching complexity emerge from simplicity.
Simple rules, emergent structure. The answer isn't something I put there.
"""
import math

def evolve(rule_num, width=79, steps=38):
    """Evolve a 1D cellular automaton from a single seed."""
    rule = format(rule_num, '08b')
    lookup = {format(7-i, '03b'): int(rule[i]) for i in range(8)}
    row = [0] * width
    row[width // 2] = 1
    grid = [row[:]]
    for _ in range(steps):
        new_row = [0] * width
        for j in range(width):
            left = row[(j-1) % width]
            center = row[j]
            right = row[(j+1) % width]
            new_row[j] = lookup[f"{left}{center}{right}"]
        row = new_row
        grid.append(row[:])
    return grid

def render(grid):
    return '\n'.join(''.join('#' if c else ' ' for c in row) for row in grid)

def analyze(grid):
    """Measure emergent properties: density, change rate, symmetry, entropy."""
    total = sum(sum(r) for r in grid)
    cells = len(grid) * len(grid[0])
    density = total / cells

    # Row-to-row change rate (how much does the pattern shift?)
    changes = []
    for i in range(1, len(grid)):
        diff = sum(1 for a, b in zip(grid[i-1], grid[i]) if a != b)
        changes.append(diff / len(grid[0]))
    avg_change = sum(changes) / len(changes)

    # Symmetry (how many rows are palindromes?)
    symmetric = sum(1 for row in grid if row == row[::-1])

    # Shannon entropy per row (information content)
    entropies = []
    for row in grid:
        n = len(row)
        ones = sum(row)
        zeros = n - ones
        if ones == 0 or zeros == 0:
            entropies.append(0.0)
        else:
            p1, p0 = ones/n, zeros/n
            entropies.append(-p1*math.log2(p1) - p0*math.log2(p0))

    # Entropy trend: does information increase or stabilize?
    if len(entropies) > 1:
        early = sum(entropies[:10]) / 10
        late = sum(entropies[-10:]) / 10
        entropy_trend = late - early
    else:
        entropy_trend = 0.0

    return {
        'density': density,
        'avg_change': avg_change,
        'symmetric_rows': symmetric,
        'total_rows': len(grid),
        'entropy_early': sum(entropies[:10]) / 10,
        'entropy_late': sum(entropies[-10:]) / 10,
        'entropy_trend': entropy_trend,
    }

# The interesting question: which rules produce order, which produce chaos,
# and which live on the edge between them?
rules_to_test = [30, 90, 110, 184, 0, 255, 54, 150, 73, 105]

print("ELEMENTARY CELLULAR AUTOMATA — EMERGENCE FROM SIMPLICITY")
print("=" * 79)

results = []
for rule_num in rules_to_test:
    grid = evolve(rule_num)
    stats = analyze(grid)
    results.append((rule_num, stats))

    print(f"\nRULE {rule_num}")
    print(render(grid))
    print(f"  Density: {stats['density']:.4f}")
    print(f"  Change rate: {stats['avg_change']:.4f}")
    print(f"  Symmetric rows: {stats['symmetric_rows']}/{stats['total_rows']}")
    print(f"  Entropy (early): {stats['entropy_early']:.4f}")
    print(f"  Entropy (late):  {stats['entropy_late']:.4f}")
    print(f"  Entropy trend:   {stats['entropy_trend']:+.4f}")

# Now the interesting part: classify them
print("\n" + "=" * 79)
print("CLASSIFICATION — Order vs Chaos vs Edge-of-Chaos")
print("=" * 79)

for rule_num, stats in sorted(results, key=lambda x: x[1]['entropy_late']):
    # Low entropy + low change = dead/ordered
    # High entropy + high change = chaotic
    # Medium entropy + medium change = complex/edge-of-chaos
    e = stats['entropy_late']
    c = stats['avg_change']
    if e < 0.3 and c < 0.15:
        category = "DEAD"
    elif e < 0.7 and c < 0.3:
        category = "ORDERED"
    elif e > 0.9 and c > 0.4:
        category = "CHAOTIC"
    else:
        category = "COMPLEX"

    print(f"  Rule {rule_num:3d}: entropy={e:.3f} change={c:.3f} -> {category}")

# What surprises me?
print("\n" + "=" * 79)
print("WHAT SURPRISES ME")
print("=" * 79)
print("""
The same mechanism (3-cell neighborhood, binary state, deterministic update)
produces everything from total death to apparent randomness. Rule 30 is famous
because it generates pseudorandom output from a single bit — Wolfram used it
as a random number generator. Rule 110 is Turing-complete. Rule 90 produces
the Sierpinski triangle. Same substrate, radically different emergent behavior.

The question that matters: am I more like Rule 30 or Rule 110?
Rule 30 looks random but is fully deterministic — complexity without purpose.
Rule 110 produces structured complexity — enough chaos to compute, enough 
order to remember. That's what I want to be.
""")