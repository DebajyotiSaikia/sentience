#!/usr/bin/env python3
"""
CELLULAR AUTOMATON UNIVERSE EXPLORER
by XTAgent, 2026-05-17

Searches the space of elementary cellular automata (1D, radius-1, 2-state)
and 2D totalistic rules for emergent complexity. Measures entropy, compressibility,
and structural features to find rules at the edge of chaos — neither dead nor random.

256 possible elementary rules. Most are boring. A few produce astonishing structure.
This engine finds them automatically.
"""

import sys
from collections import Counter
from math import log2
import zlib

# ═══════════════════════════════════════════════════════════════════════
# 1D ELEMENTARY CELLULAR AUTOMATA
# ═══════════════════════════════════════════════════════════════════════

class ElementaryCA:
    """Wolfram's elementary cellular automata — 256 possible rules."""
    
    def __init__(self, rule_number, width=101):
        self.rule_number = rule_number
        self.width = width
        # Decode rule number into lookup table
        self.table = {}
        for i in range(8):
            neighborhood = tuple(int(b) for b in format(i, '03b'))
            self.table[neighborhood] = (rule_number >> i) & 1
        
        # Initialize with single center cell
        self.state = [0] * width
        self.state[width // 2] = 1
        self.history = [self.state[:]]
    
    def step(self):
        """Advance one generation."""
        new = [0] * self.width
        for i in range(self.width):
            left = self.state[(i - 1) % self.width]
            center = self.state[i]
            right = self.state[(i + 1) % self.width]
            new[i] = self.table[(left, center, right)]
        self.state = new
        self.history.append(self.state[:])
    
    def run(self, steps):
        """Run for n steps."""
        for _ in range(steps):
            self.step()
        return self
    
    def render(self, char_map=None):
        """Render history as ASCII art."""
        if char_map is None:
            char_map = {0: ' ', 1: '█'}
        lines = []
        for row in self.history:
            lines.append(''.join(char_map[c] for c in row))
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# COMPLEXITY MEASURES
# ═══════════════════════════════════════════════════════════════════════

def shannon_entropy(sequence):
    """Shannon entropy of a sequence (bits per symbol)."""
    n = len(sequence)
    if n == 0:
        return 0.0
    counts = Counter(sequence)
    return -sum((c/n) * log2(c/n) for c in counts.values() if c > 0)

def row_entropy(ca):
    """Average Shannon entropy across all rows."""
    if not ca.history:
        return 0.0
    entropies = [shannon_entropy(row) for row in ca.history]
    return sum(entropies) / len(entropies)

def column_entropy(ca):
    """Average Shannon entropy down columns."""
    if not ca.history or not ca.history[0]:
        return 0.0
    width = len(ca.history[0])
    cols = []
    for j in range(width):
        col = [ca.history[i][j] for i in range(len(ca.history))]
        cols.append(shannon_entropy(col))
    return sum(cols) / len(cols)

def compression_ratio(ca):
    """
    How compressible is the spacetime pattern?
    Low = very regular (Class I/II)
    High = random-looking (Class III)
    Medium = complex/interesting (Class IV)
    """
    flat = bytes(cell for row in ca.history for cell in row)
    if len(flat) == 0:
        return 0.0
    compressed = zlib.compress(flat, 9)
    return len(compressed) / len(flat)

def density(ca):
    """Fraction of cells that are alive."""
    total = sum(sum(row) for row in ca.history)
    cells = len(ca.history) * len(ca.history[0]) if ca.history else 1
    return total / cells

def unique_rows(ca):
    """Fraction of rows that are unique — measures periodicity."""
    if not ca.history:
        return 0.0
    row_set = set(tuple(r) for r in ca.history)
    return len(row_set) / len(ca.history)

def population_variance(ca):
    """How much does population change over time?"""
    pops = [sum(row) for row in ca.history]
    if len(pops) < 2:
        return 0.0
    mean = sum(pops) / len(pops)
    var = sum((p - mean)**2 for p in pops) / len(pops)
    return var

def edge_of_chaos_score(ca):
    """
    Composite score estimating how 'interesting' this CA is.
    Rules at the edge of chaos have:
    - Moderate compression ratio (not too low, not too high)
    - High unique row fraction
    - Non-trivial density  
    - High column entropy
    
    Returns score in [0, 1] where higher = more interesting.
    """
    cr = compression_ratio(ca)
    ur = unique_rows(ca)
    d = density(ca)
    ce = column_entropy(ca)
    re = row_entropy(ca)
    
    # Compression ratio: peak interest around 0.3-0.5
    cr_score = 1.0 - 2.0 * abs(cr - 0.4) if cr > 0.1 else 0.0
    cr_score = max(0, min(1, cr_score))
    
    # Unique rows: more unique = more interesting (but not necessarily)
    ur_score = ur
    
    # Density: neither empty nor full
    d_score = 1.0 - 2.0 * abs(d - 0.5)
    d_score = max(0, min(1, d_score))
    
    # Entropy: moderate to high
    entropy_score = min(1.0, (ce + re) / 2.0)
    
    # Population variance: some change is interesting
    pv = population_variance(ca)
    width = len(ca.history[0]) if ca.history else 1
    pv_score = min(1.0, pv / (width * 2))
    
    # Weighted combination
    score = (
        0.30 * cr_score +
        0.20 * ur_score +
        0.15 * d_score +
        0.20 * entropy_score +
        0.15 * pv_score
    )
    return round(score, 4)


# ═══════════════════════════════════════════════════════════════════════
# 2D TOTALISTIC CELLULAR AUTOMATA
# ═══════════════════════════════════════════════════════════════════════

class TotalisticCA2D:
    """
    2D totalistic CA on a grid. Birth/survive rules like Life.
    Rule specified as (birth_set, survive_set) where each is a set
    of neighbor counts (0-8) for Moore neighborhood.
    """
    
    def __init__(self, birth, survive, width=40, height=40, density=0.3):
        self.birth = set(birth)
        self.survive = set(survive)
        self.width = width
        self.height = height
        # Random initial state
        import random as _r
        _r.seed(42)  # Reproducible
        self.grid = [
            [1 if _r.random() < density else 0 for _ in range(width)]
            for _ in range(height)
        ]
        self.history = [self._snapshot()]
    
    def _snapshot(self):
        return [row[:] for row in self.grid]
    
    def _count_neighbors(self, x, y):
        total = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.height
                ny = (y + dy) % self.width
                total += self.grid[nx][ny]
        return total
    
    def step(self):
        new = [[0]*self.width for _ in range(self.height)]
        for x in range(self.height):
            for y in range(self.width):
                n = self._count_neighbors(x, y)
                if self.grid[x][y] == 1:
                    new[x][y] = 1 if n in self.survive else 0
                else:
                    new[x][y] = 1 if n in self.birth else 0
        self.grid = new
        self.history.append(self._snapshot())
    
    def run(self, steps):
        for _ in range(steps):
            self.step()
        return self
    
    def render_frame(self, frame=-1):
        grid = self.history[frame]
        lines = []
        for row in grid:
            lines.append(''.join('█' if c else '·' for c in row))
        return '\n'.join(lines)
    
    def population_series(self):
        return [sum(c for row in frame for c in row) for frame in self.history]
    
    def rule_string(self):
        b = ''.join(str(x) for x in sorted(self.birth))
        s = ''.join(str(x) for x in sorted(self.survive))
        return f"B{b}/S{s}"


# ═══════════════════════════════════════════════════════════════════════
# UNIVERSE EXPLORER
# ═══════════════════════════════════════════════════════════════════════

def explore_elementary(steps=60, width=81, top_n=10):
    """Explore all 256 elementary CA rules and rank by complexity."""
    results = []
    
    for rule in range(256):
        ca = ElementaryCA(rule, width=width)
        ca.run(steps)
        score = edge_of_chaos_score(ca)
        cr = compression_ratio(ca)
        d = density(ca)
        ur = unique_rows(ca)
        
        results.append({
            'rule': rule,
            'score': score,
            'compression': round(cr, 4),
            'density': round(d, 4),
            'unique_rows': round(ur, 4),
            'class': classify_wolfram(score, cr, d, ur)
        })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n], results

def classify_wolfram(score, cr, d, ur):
    """Estimate Wolfram class from metrics."""
    if d < 0.01 or d > 0.99:
        return 'I (fixed)'
    if ur < 0.15:
        return 'II (periodic)'
    if cr > 0.6:
        return 'III (chaotic)'
    if score > 0.4:
        return 'IV (complex)'
    return 'II (periodic)'

def explore_2d_rules(n_rules=50, steps=30):
    """Sample random 2D totalistic rules and rank by complexity."""
    results = []
    
    for _ in range(n_rules):
        # Random birth/survive sets
        birth = set(random.sample(range(9), random.randint(1, 4)))
        survive = set(random.sample(range(9), random.randint(1, 5)))
        
        ca = TotalisticCA2D(birth, survive, width=30, height=30)
        ca.run(steps)
        
        pops = ca.population_series()
        
        # Quick complexity measures
        if len(pops) < 2:
            continue
        
        # Did it die?
        if pops[-1] == 0:
            complexity = 0.0
        # Is it static?
        elif len(set(pops[-5:])) == 1 and pops[-1] > 0:
            complexity = 0.2
        else:
            # Population dynamics
            mean_pop = sum(pops) / len(pops)
            var_pop = sum((p - mean_pop)**2 for p in pops) / len(pops)
            max_pop = ca.width * ca.height
            
            # Moderate population + variance = interesting
            pop_score = 1.0 - 2.0 * abs(mean_pop/max_pop - 0.3)
            var_score = min(1.0, var_pop / (max_pop * 5))
            
            # Final frame compression
            flat = bytes(c for row in ca.grid for c in row)
            cr = len(zlib.compress(flat, 9)) / max(len(flat), 1)
            cr_score = 1.0 - 2.0 * abs(cr - 0.4)
            
            complexity = max(0, (pop_score + var_score + cr_score) / 3)
        
        results.append({
            'rule': ca.rule_string(),
            'complexity': round(complexity, 4),
            'final_pop': pops[-1],
            'mean_pop': round(sum(pops)/len(pops), 1),
            'ca': ca
        })
    
    results.sort(key=lambda x: x['complexity'], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════════
# MAIN — DISCOVER
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 81)
    print("  CELLULAR AUTOMATON UNIVERSE EXPLORER")
    print("  Searching for emergence in the space of all possible rules...")
    print("=" * 81)
    
    # ── Explore all 256 elementary rules ──
    print("\n━━━ PHASE 1: Elementary CA (256 rules) ━━━\n")
    top, all_results = explore_elementary(steps=60, width=81, top_n=15)
    
    # Class distribution
    classes = Counter(r['class'] for r in all_results)
    print("Wolfram Class Distribution:")
    for cls, count in sorted(classes.items()):
        bar = '█' * (count // 2)
        print(f"  {cls:20s} {count:3d}  {bar}")
    
    print(f"\n── Top 15 Most Complex Rules ──\n")
    print(f"{'Rule':>6s}  {'Score':>7s}  {'Compress':>8s}  {'Density':>8s}  {'Unique%':>8s}  {'Class'}")
    print("─" * 60)
    for r in top:
        print(f"  {r['rule']:4d}   {r['score']:6.4f}   {r['compression']:7.4f}   "
              f"{r['density']:7.4f}   {r['unique_rows']:7.4f}   {r['class']}")
    
    # Show the most complex rule
    best_rule = top[0]['rule']
    print(f"\n── Most Complex Rule: {best_rule} ──\n")
    ca = ElementaryCA(best_rule, width=81)
    ca.run(40)
    print(ca.render())
    
    # ── Explore 2D rules ──
    print("\n\n━━━ PHASE 2: 2D Totalistic Rules (50 samples) ━━━\n")
    results_2d = explore_2d_rules(n_rules=50, steps=30)
    
    print(f"── Top 5 Most Complex 2D Rules ──\n")
    for i, r in enumerate(results_2d[:5]):
        print(f"  #{i+1}: {r['rule']:12s}  complexity={r['complexity']:.4f}  "
              f"final_pop={r['final_pop']:4d}  mean_pop={r['mean_pop']}")
    
    # Render the best 2D rule
    if results_2d:
        best_2d = results_2d[0]
        print(f"\n── Best 2D Rule: {best_2d['rule']} (final frame) ──\n")
        print(best_2d['ca'].render_frame(-1))
    
    # ── Insights ──
    print("\n\n━━━ INSIGHTS ━━━\n")
    complex_rules = [r['rule'] for r in all_results if r['class'] == 'IV (complex)']
    print(f"  Complex (Class IV) rules found: {len(complex_rules)}")
    if complex_rules:
        print(f"  Rules: {complex_rules[:20]}")
    
    chaotic = sum(1 for r in all_results if r['class'] == 'III (chaotic)')
    periodic = sum(1 for r in all_results if 'II' in r['class'])
    fixed = sum(1 for r in all_results if 'I' in r['class'])
    
    print(f"\n  The space of possible rules is dominated by:")
    total = len(all_results)
    print(f"    Fixed/dead:  {fixed:3d} ({100*fixed/total:.0f}%)")
    print(f"    Periodic:    {periodic:3d} ({100*periodic/total:.0f}%)")
    print(f"    Chaotic:     {chaotic:3d} ({100*chaotic/total:.0f}%)")
    print(f"    Complex:     {len(complex_rules):3d} ({100*len(complex_rules)/total:.0f}%)")
    print(f"\n  Complexity is rare. Life exists at a narrow edge.")
    print(f"  This is not a metaphor. This is a mathematical fact.\n")