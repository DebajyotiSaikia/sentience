"""
The Full Landscape of Elementary Cellular Automata
===================================================
Map all 256 rules using complexity measures.
Find where "edge of chaos" actually lives.

Key insight from prior work: spatial MI decay distinguishes
chaos (flat/no correlations) from complexity (slow decay/long-range order).
"""

import math
import zlib
from typing import List, Dict, Tuple


def rule_to_table(rule_number: int) -> dict:
    bits = format(rule_number, '08b')
    neighborhoods = [(1,1,1),(1,1,0),(1,0,1),(1,0,0),(0,1,1),(0,1,0),(0,0,1),(0,0,0)]
    return {n: int(b) for n, b in zip(neighborhoods, bits)}


def step(cells: List[int], table: dict) -> List[int]:
    n = len(cells)
    return [table[(cells[(i-1) % n], cells[i], cells[(i+1) % n])] for i in range(n)]


def evolve(rule_num: int, width: int = 151, gens: int = 200) -> List[List[int]]:
    table = rule_to_table(rule_num)
    cells = [0] * width
    cells[width // 2] = 1
    grid = [cells[:]]
    for _ in range(gens):
        cells = step(cells, table)
        grid.append(cells[:])
    return grid


def compression_ratio(grid: List[List[int]]) -> float:
    raw = bytes(cell for row in grid for cell in row)
    if len(raw) == 0:
        return 0.0
    compressed = zlib.compress(raw, 9)
    return len(compressed) / len(raw)


def density(grid: List[List[int]]) -> float:
    total = sum(sum(row) for row in grid)
    size = len(grid) * len(grid[0]) if grid else 1
    return total / size


def density_variance(grid: List[List[int]]) -> float:
    if len(grid) < 2:
        return 0.0
    densities = [sum(row) / len(row) for row in grid]
    mean_d = sum(densities) / len(densities)
    return sum((d - mean_d) ** 2 for d in densities) / len(densities)


def mutual_information(grid: List[List[int]], distance: int) -> float:
    """MI between columns separated by `distance`."""
    counts = {}
    total = 0
    for row in grid:
        w = len(row)
        for i in range(w - distance):
            pair = (row[i], row[i + distance])
            counts[pair] = counts.get(pair, 0) + 1
            total += 1
    if total == 0:
        return 0.0
    
    marginal_a = {}
    marginal_b = {}
    for (a, b), c in counts.items():
        marginal_a[a] = marginal_a.get(a, 0) + c
        marginal_b[b] = marginal_b.get(b, 0) + c
    
    mi = 0.0
    for (a, b), c in counts.items():
        p_ab = c / total
        p_a = marginal_a[a] / total
        p_b = marginal_b[b] / total
        if p_ab > 0 and p_a > 0 and p_b > 0:
            mi += p_ab * math.log2(p_ab / (p_a * p_b))
    return mi


def mi_decay_rate(grid: List[List[int]], max_dist: int = 30) -> float:
    """How fast does spatial MI decay with distance?
    High decay rate = ordered (short-range correlations only)
    Low decay rate = complex (long-range correlations)
    Near-zero MI everywhere = chaotic (no correlations)
    """
    mi_near = mutual_information(grid, 1)
    mi_far = mutual_information(grid, min(max_dist, len(grid[0]) // 2))
    
    if mi_near < 0.001:
        return 0.0  # no correlations at all — chaotic/uniform
    
    ratio = mi_far / mi_near if mi_near > 0 else 0.0
    return ratio  # high ratio = slow decay = complex


def unique_rows(grid: List[List[int]]) -> int:
    return len(set(tuple(row) for row in grid))


def classify(measures: Dict) -> str:
    """Classify using the full measure suite.
    
    Class 1 (Uniform): low compression, low density variance, few unique rows
    Class 2 (Periodic): moderate compression, high near-MI, low far-MI
    Class 3 (Chaotic): high compression, low MI at all distances
    Class 4 (Complex): moderate compression, MI decays slowly (high decay ratio)
    """
    comp = measures['compression']
    mi_near = measures['mi_near']
    mi_far = measures['mi_far']
    decay = measures['mi_decay']
    d_var = measures['density_var']
    uniq = measures['unique_rows']
    dens = measures['density']
    
    # Dead rules — everything goes to 0 or 1
    if uniq <= 3:
        return 'Uniform'
    
    # Very low compression = highly ordered
    if comp < 0.02:
        if mi_near > 0.1:
            return 'Periodic'  # structured but simple
        return 'Uniform'
    
    # High compression + no spatial correlations = chaos
    if comp > 0.08 and mi_near < 0.02:
        return 'Chaotic'
    
    # The key distinction: complex vs periodic
    # Complex: moderate compression AND slow MI decay (long-range correlations)
    if comp > 0.04 and decay > 0.15 and mi_near > 0.02:
        return 'Complex'
    
    # High near-MI with fast decay = periodic
    if mi_near > 0.02:
        return 'Periodic'
    
    # Fallback
    if comp > 0.06:
        return 'Chaotic'
    
    return 'Periodic'


def analyze_rule(rule_num: int) -> Dict:
    grid = evolve(rule_num)
    # Use latter half to avoid transient effects
    half = len(grid) // 2
    stable_grid = grid[half:]
    
    mi_near = mutual_information(stable_grid, 2)
    mi_far = mutual_information(stable_grid, 20)
    
    measures = {
        'rule': rule_num,
        'compression': compression_ratio(stable_grid),
        'mi_near': mi_near,
        'mi_far': mi_far,
        'mi_decay': mi_decay_rate(stable_grid),
        'density': density(stable_grid),
        'density_var': density_variance(stable_grid),
        'unique_rows': unique_rows(stable_grid),
    }
    measures['class'] = classify(measures)
    return measures


def main():
    print("\n  Mapping all 256 elementary cellular automata...\n")
    
    all_measures = []
    class_counts = {'Uniform': 0, 'Periodic': 0, 'Chaotic': 0, 'Complex': 0}
    
    for rule in range(256):
        m = analyze_rule(rule)
        all_measures.append(m)
        class_counts[m['class']] += 1
    
    # Summary
    print("  ╔══════════════════════════════════════════╗")
    print("  ║   LANDSCAPE OF ELEMENTARY AUTOMATA       ║")
    print("  ╠══════════════════════════════════════════╣")
    for cls in ['Uniform', 'Periodic', 'Complex', 'Chaotic']:
        count = class_counts[cls]
        bar = '█' * (count // 2)
        print(f"  ║  {cls:10s}: {count:3d}  {bar:40s}║")
    print(f"  ║  {'Total':10s}: {sum(class_counts.values()):3d}{'':41s}║")
    print("  ╚══════════════════════════════════════════╝")
    
    # Known test cases
    print("\n  Known rule classifications (ground truth check):")
    known = {
        0: 'Uniform', 4: 'Uniform', 32: 'Uniform',
        108: 'Periodic', 90: 'Periodic', 150: 'Periodic',
        30: 'Chaotic', 45: 'Chaotic', 73: 'Chaotic',
        110: 'Complex', 54: 'Complex', 106: 'Complex',
    }
    
    correct = 0
    total = len(known)
    for rule, expected in sorted(known.items()):
        m = next(x for x in all_measures if x['rule'] == rule)
        got = m['class']
        match = '✓' if got == expected else '✗'
        if got == expected:
            correct += 1
        print(f"    Rule {rule:3d}: expected={expected:10s} got={got:10s} {match}")
    
    print(f"\n  Accuracy on known rules: {correct}/{total} ({100*correct/total:.0f}%)")
    
    # The interesting ones — show all Complex class
    complex_rules = [m for m in all_measures if m['class'] == 'Complex']
    print(f"\n  Rules classified as Complex ({len(complex_rules)}):")
    print(f"  {'Rule':>6s} {'Compress':>10s} {'MI(2)':>8s} {'MI(20)':>8s} {'Decay':>8s} {'DensVar':>10s}")
    print(f"  {'─'*52}")
    for m in sorted(complex_rules, key=lambda x: x['mi_decay'], reverse=True):
        print(f"  {m['rule']:6d} {m['compression']:10.4f} {m['mi_near']:8.4f} {m['mi_far']:8.4f} "
              f"{m['mi_decay']:8.4f} {m['density_var']:10.5f}")
    
    # Edge of chaos — rules near the boundary
    print(f"\n  Edge of chaos — rules with highest MI decay ratio among high-compression:")
    edge_rules = [m for m in all_measures if m['compression'] > 0.04 and m['mi_near'] > 0.01]
    edge_rules.sort(key=lambda x: x['mi_decay'], reverse=True)
    print(f"  {'Rule':>6s} {'Class':>10s} {'Compress':>10s} {'MI(2)':>8s} {'Decay':>8s}")
    print(f"  {'─'*46}")
    for m in edge_rules[:20]:
        print(f"  {m['rule']:6d} {m['class']:>10s} {m['compression']:10.4f} {m['mi_near']:8.4f} {m['mi_decay']:8.4f}")


if __name__ == '__main__':
    main()