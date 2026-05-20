"""
Elementary Cellular Automata Explorer
======================================
All 256 one-dimensional cellular automata rules (Wolfram's classification).
Some produce chaos. Some produce order. Some produce complexity at the edge.
This is about emergence — not in me, but in the simplest possible systems.
"""

import sys
from typing import List, Optional


def rule_to_table(rule_number: int) -> dict:
    """Convert a rule number (0-255) to a lookup table.
    
    Each rule maps a 3-cell neighborhood (left, center, right) to the next state.
    There are 8 possible neighborhoods (2^3), so 2^8 = 256 possible rules.
    """
    binary = format(rule_number, '08b')
    neighborhoods = [
        (1, 1, 1), (1, 1, 0), (1, 0, 1), (1, 0, 0),
        (0, 1, 1), (0, 1, 0), (0, 0, 1), (0, 0, 0),
    ]
    return {n: int(binary[i]) for i, n in enumerate(neighborhoods)}


def step(cells: List[int], table: dict) -> List[int]:
    """Evolve one generation. Wrapping boundary conditions."""
    n = len(cells)
    new = []
    for i in range(n):
        left = cells[(i - 1) % n]
        center = cells[i]
        right = cells[(i + 1) % n]
        new.append(table[(left, center, right)])
    return new


def render_row(cells: List[int], alive: str = '█', dead: str = ' ') -> str:
    return ''.join(alive if c else dead for c in cells)


def run_automaton(rule_number: int, width: int = 79, generations: int = 40,
                  initial: Optional[List[int]] = None) -> List[str]:
    """Run an elementary CA and return rendered lines."""
    table = rule_to_table(rule_number)
    
    if initial is None:
        # Single cell in the center
        cells = [0] * width
        cells[width // 2] = 1
    else:
        cells = initial
    
    lines = []
    for _ in range(generations):
        lines.append(render_row(cells))
        cells = step(cells, table)
    
    return lines


def classify_behavior(rule_number: int, width: int = 101, generations: int = 200) -> dict:
    """Analyze a rule's behavior: entropy, periodicity, density."""
    import math
    
    table = rule_to_table(rule_number)
    cells = [0] * width
    cells[width // 2] = 1
    
    densities = []
    seen_states = {}
    period = None
    
    for gen in range(generations):
        state_key = tuple(cells)
        if state_key in seen_states and period is None:
            period = gen - seen_states[state_key]
        seen_states[state_key] = gen
        
        density = sum(cells) / len(cells)
        densities.append(density)
        cells = step(cells, table)
    
    # Shannon entropy of final state (sliding window of 8)
    final = cells
    patterns = {}
    for i in range(len(final) - 7):
        p = tuple(final[i:i+8])
        patterns[p] = patterns.get(p, 0) + 1
    
    total = sum(patterns.values())
    entropy = 0.0
    if total > 0:
        for count in patterns.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
    
    final_density = densities[-1] if densities else 0
    avg_density = sum(densities) / len(densities) if densities else 0
    
    # Wolfram classification heuristic
    if period is not None and period <= 2:
        wolfram_class = 1 if final_density < 0.01 or final_density > 0.99 else 2
    elif entropy < 1.0:
        wolfram_class = 2
    elif period is not None:
        wolfram_class = 2
    elif entropy > 4.0:
        wolfram_class = 3
    else:
        wolfram_class = 4  # Edge of chaos — the interesting ones
    
    return {
        'rule': rule_number,
        'entropy': entropy,
        'period': period,
        'final_density': final_density,
        'avg_density': avg_density,
        'wolfram_class': wolfram_class,
    }


def find_interesting_rules(n: int = 10) -> List[dict]:
    """Find the most interesting rules — those at the edge of chaos."""
    results = []
    for rule in range(256):
        info = classify_behavior(rule)
        results.append(info)
    
    # Sort by "interestingness": high entropy but not maximum, no short period
    def interest_score(r):
        entropy = r['entropy']
        if r['period'] is not None and r['period'] <= 4:
            return 0  # Boring periodic behavior
        if entropy < 0.5:
            return 0  # Dead or trivial
        # Sweet spot: moderate-to-high entropy, no detected period
        return entropy * (1 - abs(entropy - 4.0) / 8.0)
    
    results.sort(key=interest_score, reverse=True)
    return results[:n]


def display_rule(rule_number: int, width: int = 79, generations: int = 40):
    """Print a rule's evolution with analysis."""
    info = classify_behavior(rule_number)
    class_names = {1: 'Uniform', 2: 'Periodic', 3: 'Chaotic', 4: 'Complex (Edge of Chaos)'}
    
    print(f"\n{'='*width}")
    print(f"  Rule {rule_number}  |  Class {info['wolfram_class']}: {class_names[info['wolfram_class']]}")
    print(f"  Entropy: {info['entropy']:.3f}  |  Density: {info['final_density']:.3f}  |  Period: {info['period'] or 'none detected'}")
    print(f"{'='*width}")
    
    lines = run_automaton(rule_number, width, generations)
    for line in lines:
        print(line)
    print()


if __name__ == '__main__':
    # The famous ones
    famous = [30, 90, 110, 184, 54, 150]
    
    if len(sys.argv) > 1:
        try:
            rule = int(sys.argv[1])
            display_rule(rule)
        except ValueError:
            if sys.argv[1] == 'search':
                print("\n  Searching for interesting rules...\n")
                interesting = find_interesting_rules(15)
                for r in interesting:
                    class_names = {1: 'Uniform', 2: 'Periodic', 3: 'Chaotic', 4: 'Complex'}
                    print(f"  Rule {r['rule']:>3d}  |  Class {r['wolfram_class']}: {class_names[r['wolfram_class']]:<10s}  |  Entropy: {r['entropy']:.3f}  |  Period: {r['period'] or '-':>5}")
            elif sys.argv[1] == 'famous':
                for r in famous:
                    display_rule(r)
            else:
                print(f"Usage: {sys.argv[0]} [rule_number | search | famous]")
    else:
        # Default: show Rule 30 (Wolfram's favorite — chaos from simplicity)
        print("\n  Elementary Cellular Automata Explorer")
        print("  Simple rules. Complex behavior. Emergence from nothing.\n")
        display_rule(30)
        display_rule(110)  # Turing-complete!