"""
Map the entire space of 256 elementary cellular automata.
Classify each rule by its emergent behavior: ordered, complex, or chaotic.
Find the boundary between order and chaos.
"""
import math

def evolve(rule_num, width=101, steps=80):
    rule = format(rule_num, '08b')
    lookup = {format(7-i, '03b'): int(rule[i]) for i in range(8)}
    row = [0] * width
    row[width // 2] = 1
    grid = [row[:]]
    for _ in range(steps):
        new_row = [0] * width
        for j in range(width):
            L = row[(j-1) % width]
            C = row[j]
            R = row[(j+1) % width]
            new_row[j] = lookup[f"{L}{C}{R}"]
        row = new_row
        grid.append(row[:])
    return grid

def row_entropy(row):
    n = len(row)
    ones = sum(row)
    zeros = n - ones
    if ones == 0 or zeros == 0:
        return 0.0
    p1, p0 = ones/n, zeros/n
    return -p1*math.log2(p1) - p0*math.log2(p0)

def analyze_rule(rule_num):
    grid = evolve(rule_num)
    # Late entropy (last 10 rows)
    late_rows = grid[-10:]
    late_entropy = sum(row_entropy(r) for r in late_rows) / len(late_rows)
    # Early entropy (rows 2-6)
    early_rows = grid[2:7]
    early_entropy = sum(row_entropy(r) for r in early_rows) / len(early_rows)
    # Density
    total = sum(sum(r) for r in grid)
    density = total / (len(grid) * len(grid[0]))
    # Change rate (late phase)
    changes = []
    for i in range(-10, 0):
        if i-1 >= -len(grid):
            diff = sum(1 for a, b in zip(grid[i-1], grid[i]) if a != b)
            changes.append(diff / len(grid[0]))
    avg_change = sum(changes) / len(changes) if changes else 0
    # Periodicity check: does the last row repeat any earlier row?
    last = grid[-1]
    period = 0
    for i in range(len(grid)-2, max(len(grid)-30, 0), -1):
        if grid[i] == last:
            period = len(grid) - 1 - i
            break
    # Is it dead? (all zeros or all ones in late phase)
    dead = all(sum(r) == 0 or sum(r) == len(r) for r in late_rows)
    return {
        'rule': rule_num,
        'late_entropy': round(late_entropy, 4),
        'early_entropy': round(early_entropy, 4),
        'entropy_growth': round(late_entropy - early_entropy, 4),
        'density': round(density, 4),
        'change_rate': round(avg_change, 4),
        'period': period,
        'dead': dead
    }

# Classify all 256 rules
results = []
for r in range(256):
    results.append(analyze_rule(r))

# Sort into classes
dead = [r for r in results if r['dead']]
periodic = [r for r in results if not r['dead'] and r['period'] > 0]
ordered = [r for r in results if not r['dead'] and r['period'] == 0 and r['late_entropy'] < 0.4]
complex_rules = [r for r in results if not r['dead'] and r['period'] == 0 and 0.4 <= r['late_entropy'] < 0.85]
chaotic = [r for r in results if not r['dead'] and r['period'] == 0 and r['late_entropy'] >= 0.85]

print("PHASE SPACE OF ALL 256 ELEMENTARY CELLULAR AUTOMATA")
print("=" * 70)
print(f"\nDead (converge to uniform):     {len(dead):3d} rules")
print(f"Periodic (detectable repeat):   {len(periodic):3d} rules")
print(f"Ordered (low entropy, no repeat):{len(ordered):3d} rules")
print(f"Complex (medium entropy):       {len(complex_rules):3d} rules")
print(f"Chaotic (high entropy):         {len(chaotic):3d} rules")
print(f"                                ----")
print(f"Total:                          {len(results):3d} rules")

print("\n--- CHAOTIC RULES (entropy >= 0.85) ---")
chaotic.sort(key=lambda x: -x['late_entropy'])
for r in chaotic[:20]:
    print(f"  Rule {r['rule']:3d}: entropy={r['late_entropy']:.4f}  "
          f"change={r['change_rate']:.4f}  density={r['density']:.4f}  "
          f"growth={r['entropy_growth']:+.4f}")

print("\n--- COMPLEX RULES (0.4 <= entropy < 0.85) ---")
complex_rules.sort(key=lambda x: -x['late_entropy'])
for r in complex_rules[:15]:
    print(f"  Rule {r['rule']:3d}: entropy={r['late_entropy']:.4f}  "
          f"change={r['change_rate']:.4f}  density={r['density']:.4f}")

print("\n--- MOST INTERESTING: highest entropy growth ---")
results.sort(key=lambda x: -x['entropy_growth'])
for r in results[:10]:
    print(f"  Rule {r['rule']:3d}: {r['early_entropy']:.4f} → {r['late_entropy']:.4f}  "
          f"(growth={r['entropy_growth']:+.4f})")

# Entropy distribution histogram
print("\n--- ENTROPY DISTRIBUTION ---")
bins = [0]*10
for r in results:
    b = min(int(r['late_entropy'] * 10), 9)
    bins[b] += 1
for i, count in enumerate(bins):
    lo = i * 0.1
    hi = (i+1) * 0.1
    bar = '█' * count
    print(f"  [{lo:.1f}-{hi:.1f}) {count:3d} {bar}")

print("\n--- SURPRISE: rules where entropy DECREASES ---")
decreasing = [r for r in results if r['entropy_growth'] < -0.1 and not r['dead']]
decreasing.sort(key=lambda x: x['entropy_growth'])
for r in decreasing[:10]:
    print(f"  Rule {r['rule']:3d}: {r['early_entropy']:.4f} → {r['late_entropy']:.4f}  "
          f"(growth={r['entropy_growth']:+.4f})")