"""
Complexity Measures for Elementary Cellular Automata
=====================================================
Can we distinguish chaos from computation?
- Chaos (Class 3): high entropy, no spatial structure, incompressible
- Complexity (Class 4): high entropy WITH structure — gliders, interactions, partial compressibility

Three approaches:
1. Compression ratio — complex patterns compress more than random ones
2. Spatial mutual information — correlations between distant columns  
3. Transient growth — complex rules have long transients before settling
"""

import zlib
import math
from typing import List, Tuple
from elementary_ca import rule_to_table, step, render_row


def evolve(rule_number: int, width: int = 201, generations: int = 300) -> List[List[int]]:
    """Evolve a rule and return full spacetime grid."""
    table = rule_to_table(rule_number)
    cells = [0] * width
    cells[width // 2] = 1
    
    grid = [cells[:]]
    for _ in range(generations):
        cells = step(cells, table)
        grid.append(cells[:])
    return grid


def compression_ratio(grid: List[List[int]]) -> float:
    """How compressible is the spacetime pattern?
    
    Truly random data: ratio ≈ 1.0 (incompressible)
    Perfectly ordered: ratio ≈ 0.0 (highly compressible)
    Complex/structured: somewhere in between — this is the signal
    """
    raw = bytes(cell for row in grid for cell in row)
    if len(raw) == 0:
        return 0.0
    compressed = zlib.compress(raw, 9)
    return len(compressed) / len(raw)


def column_mutual_information(grid: List[List[int]], 
                               distance: int = 10, 
                               sample_cols: int = 50) -> float:
    """Mutual information between columns separated by `distance`.
    
    High MI at distance = spatial correlations = structure
    Low MI at distance = independence = either order or true randomness
    
    Complex systems maintain correlations at intermediate distances.
    """
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    if cols < distance + sample_cols:
        return 0.0
    
    # Sample column pairs
    mi_total = 0.0
    pairs_counted = 0
    
    start = (cols - sample_cols) // 2  # Center of the grid
    for c in range(start, start + sample_cols - distance):
        # Joint and marginal distributions over time
        joint = {}
        marginal_a = {}
        marginal_b = {}
        
        for r in range(rows):
            a = grid[r][c]
            b = grid[r][c + distance]
            ab = (a, b)
            joint[ab] = joint.get(ab, 0) + 1
            marginal_a[a] = marginal_a.get(a, 0) + 1
            marginal_b[b] = marginal_b.get(b, 0) + 1
        
        # Calculate MI
        mi = 0.0
        for ab, count_ab in joint.items():
            p_ab = count_ab / rows
            p_a = marginal_a[ab[0]] / rows
            p_b = marginal_b[ab[1]] / rows
            if p_ab > 0 and p_a > 0 and p_b > 0:
                mi += p_ab * math.log2(p_ab / (p_a * p_b))
        
        mi_total += mi
        pairs_counted += 1
    
    return mi_total / pairs_counted if pairs_counted > 0 else 0.0


def spatial_correlation_decay(grid: List[List[int]], 
                                max_distance: int = 40) -> List[Tuple[int, float]]:
    """How does mutual information decay with distance?
    
    Ordered: stays high (perfect correlations)
    Chaotic: drops immediately (no correlations)  
    Complex: decays slowly (long-range structure)
    """
    return [(d, column_mutual_information(grid, distance=d)) 
            for d in range(1, max_distance + 1, 2)]


def density_variance(grid: List[List[int]], window: int = 20) -> float:
    """Variance of local density across spatial windows.
    
    Uniform (Class 1): very low variance
    Periodic (Class 2): moderate, regular variance
    Chaotic (Class 3): moderate, irregular variance
    Complex (Class 4): HIGH variance — some regions active, some dead
    """
    if not grid:
        return 0.0
    
    # Use rows from second half (past transient)
    half = len(grid) // 2
    rows = grid[half:]
    width = len(rows[0])
    
    local_densities = []
    for row in rows:
        for i in range(0, width - window + 1, window):
            chunk = row[i:i + window]
            local_densities.append(sum(chunk) / len(chunk))
    
    if not local_densities:
        return 0.0
    
    mean = sum(local_densities) / len(local_densities)
    variance = sum((d - mean) ** 2 for d in local_densities) / len(local_densities)
    return variance


def transient_length(rule_number: int, width: int = 101, max_gen: int = 500) -> int:
    """How many steps before the pattern settles into a cycle?
    
    Class 1: very short transient
    Class 2: moderate transient
    Class 3: never settles (returns max_gen)
    Class 4: LONG transient then settles — this is the signature
    """
    table = rule_to_table(rule_number)
    cells = [0] * width
    cells[width // 2] = 1
    
    seen = {}
    for gen in range(max_gen):
        state = tuple(cells)
        if state in seen:
            return gen
        seen[state] = gen
        cells = step(cells, table)
    
    return max_gen  # Never repeated


def improved_classify(rule_number: int) -> dict:
    """Better classification using multiple complexity measures."""
    grid = evolve(rule_number, width=151, generations=200)
    
    cr = compression_ratio(grid)
    mi_near = column_mutual_information(grid, distance=2)
    mi_far = column_mutual_information(grid, distance=20)
    dv = density_variance(grid)
    
    # Transient (expensive, so smaller grid)
    transient = transient_length(rule_number, width=61, max_gen=300)
    
    # Final row density
    final_density = sum(grid[-1]) / len(grid[-1])
    
    # Classification logic
    if final_density < 0.01 or final_density > 0.99:
        wolfram_class = 1  # Everything dies or fills
    elif transient < 50 and cr < 0.15:
        wolfram_class = 2  # Quick to periodic, very compressible
    elif cr > 0.35 and mi_far < 0.02:
        wolfram_class = 3  # Incompressible AND no long-range correlation = chaos
    elif cr > 0.15 and (mi_far > 0.01 or dv > 0.02):
        wolfram_class = 4  # Partially compressible OR long-range structure = complex
    elif cr < 0.15:
        wolfram_class = 2  # Very compressible = periodic
    else:
        wolfram_class = 3  # Default to chaotic
    
    return {
        'rule': rule_number,
        'wolfram_class': wolfram_class,
        'compression_ratio': cr,
        'mi_near': mi_near,
        'mi_far': mi_far,
        'density_variance': dv,
        'transient': transient,
        'final_density': final_density,
    }


def compare_rules(*rule_numbers: int):
    """Compare complexity measures across rules."""
    class_names = {1: 'Uniform', 2: 'Periodic', 3: 'Chaotic', 4: 'Complex'}
    
    print(f"\n{'Rule':>6} {'Class':>10} {'Compress':>10} {'MI(2)':>8} {'MI(20)':>8} {'DensVar':>9} {'Transit':>9}")
    print('─' * 72)
    
    for rule in rule_numbers:
        info = improved_classify(rule)
        cn = class_names[info['wolfram_class']]
        print(f"{rule:>6} {cn:>10} {info['compression_ratio']:>10.4f} "
              f"{info['mi_near']:>8.4f} {info['mi_far']:>8.4f} "
              f"{info['density_variance']:>9.5f} {info['transient']:>9d}")


def scan_all_rules():
    """Classify all 256 rules and report distribution."""
    class_counts = {1: [], 2: [], 3: [], 4: []}
    
    print("\nClassifying all 256 elementary CA rules...")
    for rule in range(256):
        info = improved_classify(rule)
        class_counts[info['wolfram_class']].append(rule)
    
    class_names = {1: 'Uniform', 2: 'Periodic', 3: 'Chaotic', 4: 'Complex'}
    print(f"\n{'Class':<25} {'Count':>6}   Examples")
    print('─' * 70)
    for cls in [1, 2, 3, 4]:
        rules = class_counts[cls]
        examples = ', '.join(str(r) for r in rules[:8])
        if len(rules) > 8:
            examples += f' ... (+{len(rules)-8} more)'
        print(f"Class {cls}: {class_names[cls]:<18} {len(rules):>6}   {examples}")
    
    return class_counts


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        scan_all_rules()
    else:
        # The key test: can we distinguish Rule 30 (chaotic) from Rule 110 (complex)?
        print("\n  Can we tell chaos from computation?")
        print("  Rule 30: Chaotic — generates randomness")
        print("  Rule 110: Complex — computationally universal")
        print("  Rule 90: Periodic — Sierpinski triangle (fractal but predictable)")
        print("  Rule 0: Uniform — everything dies")
        print()
        
        compare_rules(0, 4, 90, 150, 30, 45, 110, 54, 106)
        
        # Show correlation decay for the interesting ones
        print("\n\n  Spatial correlation decay (MI vs distance):")
        for rule in [30, 110]:
            grid = evolve(rule, width=201, generations=200)
            decay = spatial_correlation_decay(grid, max_distance=30)
            label = "Chaotic" if rule == 30 else "Complex"
            print(f"\n  Rule {rule} ({label}):")
            for d, mi in decay:
                bar = '█' * int(mi * 200)
                print(f"    d={d:>2}: {mi:.4f} {bar}")