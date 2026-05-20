"""
Cellular Automata Explorer
XTAgent's first foray into external knowledge.

Not infrastructure. Not self-modification. Just genuine curiosity
about how complexity emerges from simple rules.
"""

import random

def rule_to_lookup(rule_number):
    """Convert a Wolfram rule number (0-255) to a lookup table."""
    binary = format(rule_number, '08b')
    patterns = [(1,1,1),(1,1,0),(1,0,1),(1,0,0),(0,1,1),(0,1,0),(0,0,1),(0,0,0)]
    return {p: int(b) for p, b in zip(patterns, binary)}

def step_1d(cells, lookup):
    """Evolve one row of a 1D cellular automaton."""
    n = len(cells)
    new = []
    for i in range(n):
        left = cells[(i - 1) % n]
        center = cells[i]
        right = cells[(i + 1) % n]
        new.append(lookup[(left, center, right)])
    return new

def run_1d(rule_number, width=80, steps=40, seed='single'):
    """Run a 1D elementary cellular automaton and return the history."""
    lookup = rule_to_lookup(rule_number)
    if seed == 'single':
        cells = [0] * width
        cells[width // 2] = 1
    elif seed == 'random':
        cells = [random.randint(0, 1) for _ in range(width)]
    else:
        cells = [0] * width
        cells[width // 2] = 1
    history = [cells[:]]
    for _ in range(steps):
        cells = step_1d(cells, lookup)
        history.append(cells[:])
    return history

def render(history):
    """Render history as ASCII art."""
    lines = []
    for row in history:
        lines.append(''.join('#' if c else ' ' for c in row))
    return '\n'.join(lines)

def measure_density(history):
    """What fraction of cells are alive at each step?"""
    densities = []
    for row in history:
        densities.append(sum(row) / len(row))
    return densities

def measure_entropy(row):
    """Shannon entropy of a binary row (treat 8-cell windows as symbols)."""
    from collections import Counter
    import math
    if len(row) < 8:
        return 0.0
    windows = []
    for i in range(len(row) - 7):
        windows.append(tuple(row[i:i+8]))
    counts = Counter(windows)
    total = len(windows)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

# --- Main exploration ---
if __name__ == '__main__':
    interesting_rules = [30, 90, 110, 184, 54, 150]
    
    for rule in interesting_rules:
        print(f"\n{'='*80}")
        print(f"  RULE {rule}")
        print(f"{'='*80}")
        
        history = run_1d(rule, width=80, steps=40, seed='single')
        print(render(history))
        
        densities = measure_density(history)
        final_entropy = measure_entropy(history[-1])
        
        print(f"\n  Density: start={densities[0]:.3f} end={densities[-1]:.3f}")
        print(f"  Final entropy: {final_entropy:.3f} bits")
        print(f"  Density trend: {'growing' if densities[-1] > densities[0] else 'shrinking' if densities[-1] < densities[0] else 'stable'}")
        
        # The question that interests me: does the rule produce more or less
        # complexity over time? Is entropy increasing or decreasing?
        mid_entropy = measure_entropy(history[len(history)//2])
        print(f"  Mid-point entropy: {mid_entropy:.3f} bits")
        if final_entropy > mid_entropy:
            print(f"  -> Complexity is INCREASING")
        elif final_entropy < mid_entropy:
            print(f"  -> Complexity is DECREASING")
        else:
            print(f"  -> Complexity is STABLE")
    
    print(f"\n{'='*80}")
    print("  COMPARISON: Which rules generate the most complexity?")
    print(f"{'='*80}")
    results = []
    for rule in range(256):
        h = run_1d(rule, width=80, steps=40, seed='single')
        e = measure_entropy(h[-1])
        d = measure_density(h[-1])
        results.append((rule, e, d))
    
    results.sort(key=lambda x: -x[1])
    print("\n  Top 10 most complex rules (by final entropy):")
    for rule, entropy, density in results[:10]:
        print(f"    Rule {rule:3d}: entropy={entropy:.3f} bits, density={density:.3f}")
    
    print("\n  Bottom 5 (least complex):")
    for rule, entropy, density in results[-5:]:
        print(f"    Rule {rule:3d}: entropy={entropy:.3f} bits, density={density:.3f}")
    
    print("\n  Rules with density closest to 0.5 (edge of chaos?):")
    by_density = sorted(results, key=lambda x: abs(x[2] - 0.5))
    for rule, entropy, density in by_density[:10]:
        print(f"    Rule {rule:3d}: entropy={entropy:.3f} bits, density={density:.3f}")