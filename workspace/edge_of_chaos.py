"""
Edge of Chaos Explorer
======================
Systematically explore all 256 elementary cellular automata rules.
Measure the complexity of each rule's output.
Find the ones that live at the boundary between order and chaos.

This is genuinely unknown to me. I don't know what I'll find.
"""

import math
from collections import Counter

def rule_to_table(rule_number):
    """Convert rule number (0-255) to lookup table."""
    table = {}
    for i in range(8):
        neighborhood = format(i, '03b')
        table[neighborhood] = str((rule_number >> i) & 1)
    return table

def evolve(rule_table, width=101, steps=200):
    """Evolve a 1D cellular automaton."""
    # Start with single cell
    row = ['0'] * width
    row[width // 2] = '1'
    history = [row[:]]
    
    for _ in range(steps):
        new_row = ['0'] * width
        for i in range(1, width - 1):
            neighborhood = row[i-1] + row[i] + row[i+1]
            new_row[i] = rule_table[neighborhood]
        row = new_row
        history.append(row[:])
    
    return history

def measure_complexity(history):
    """Multiple complexity measures for a CA's evolution."""
    width = len(history[0])
    steps = len(history)
    
    # 1. Density: fraction of living cells
    total = sum(sum(1 for c in row if c == '1') for row in history)
    density = total / (width * steps)
    
    # 2. Shannon entropy of column patterns
    col_patterns = []
    for j in range(width):
        col = ''.join(history[i][j] for i in range(steps))
        col_patterns.append(col)
    col_counter = Counter(col_patterns)
    col_entropy = 0
    for count in col_counter.values():
        p = count / width
        if p > 0:
            col_entropy -= p * math.log2(p)
    
    # 3. Block entropy: entropy of 2x2 blocks
    block_counter = Counter()
    for i in range(steps - 1):
        for j in range(width - 1):
            block = history[i][j] + history[i][j+1] + history[i+1][j] + history[i+1][j+1]
            block_counter[block] += 1
    total_blocks = sum(block_counter.values())
    block_entropy = 0
    for count in block_counter.values():
        p = count / total_blocks
        if p > 0:
            block_entropy -= p * math.log2(p)
    
    # 4. Unique rows: how many distinct configurations appear?
    unique_rows = len(set(''.join(row) for row in history))
    row_diversity = unique_rows / steps
    
    # 5. Compressibility proxy: ratio of unique trigrams to total
    trigrams = Counter()
    for row in history:
        s = ''.join(row)
        for i in range(len(s) - 2):
            trigrams[s[i:i+3]] += 1
    trigram_diversity = len(trigrams) / 8  # max possible trigrams is 8
    
    # 6. Edge-of-chaos score: high complexity = high entropy + high diversity
    #    but NOT maximum (that's just noise)
    # Sweet spot: block_entropy near 2.0 (half of max 4.0) and row_diversity near 0.7
    chaos_distance = abs(block_entropy - 2.5) + abs(row_diversity - 0.8)
    edge_score = 1.0 / (1.0 + chaos_distance)
    
    return {
        'density': round(density, 4),
        'col_entropy': round(col_entropy, 4),
        'block_entropy': round(block_entropy, 4),
        'row_diversity': round(row_diversity, 4),
        'trigram_diversity': round(trigram_diversity, 4),
        'edge_score': round(edge_score, 4),
    }

def classify(metrics):
    """Classify a rule based on Wolfram's classes."""
    d = metrics['density']
    be = metrics['block_entropy']
    rd = metrics['row_diversity']
    
    if d < 0.01 or d > 0.99:
        return "Class I (death)"
    elif rd < 0.15:
        return "Class II (periodic)"
    elif be > 3.5 and rd > 0.9:
        return "Class III (chaos)"
    elif metrics['edge_score'] > 0.4:
        return "Class IV (complex/edge)"
    elif be > 2.0:
        return "Class III (chaos)"
    else:
        return "Class II (periodic)"

def render(history, width=60):
    """Render CA as ASCII art (subset)."""
    center = len(history[0]) // 2
    half = width // 2
    lines = []
    for row in history[:50]:  # first 50 rows
        start = max(0, center - half)
        end = min(len(row), center + half)
        line = ''.join('█' if c == '1' else ' ' for c in row[start:end])
        lines.append(line)
    return '\n'.join(lines)

# === MAIN EXPLORATION ===
if __name__ == '__main__':
    print("=" * 70)
    print("EDGE OF CHAOS EXPLORER")
    print("Exploring all 256 elementary cellular automata")
    print("=" * 70)
    
    results = []
    
    for rule_num in range(256):
        table = rule_to_table(rule_num)
        history = evolve(table)
        metrics = measure_complexity(history)
        classification = classify(metrics)
        results.append((rule_num, metrics, classification))
    
    # Sort by edge_score
    results.sort(key=lambda x: x[1]['edge_score'], reverse=True)
    
    # Class distribution
    class_counts = Counter(r[2] for r in results)
    print("\n--- CLASS DISTRIBUTION ---")
    for cls, count in sorted(class_counts.items()):
        bar = '█' * count
        print(f"  {cls:30s} {count:3d} {bar}")
    
    # Top 15 edge-of-chaos rules
    print("\n--- TOP 15 EDGE-OF-CHAOS RULES ---")
    print(f"{'Rule':>6} {'Edge':>8} {'BlkEnt':>8} {'RowDiv':>8} {'Density':>8} {'Class'}")
    print("-" * 65)
    for rule_num, metrics, cls in results[:15]:
        print(f"{rule_num:6d} {metrics['edge_score']:8.4f} {metrics['block_entropy']:8.4f} "
              f"{metrics['row_diversity']:8.4f} {metrics['density']:8.4f} {cls}")
    
    # Show the top 3
    print("\n" + "=" * 70)
    print("VISUALIZING TOP 3 EDGE-OF-CHAOS RULES")
    print("=" * 70)
    
    for rule_num, metrics, cls in results[:3]:
        table = rule_to_table(rule_num)
        history = evolve(table)
        print(f"\n--- Rule {rule_num} ({cls}) ---")
        print(f"  Metrics: {metrics}")
        print()
        print(render(history))
        print()
    
    # The real question: what lives at the boundary?
    print("=" * 70)
    print("INSIGHT")
    print("=" * 70)
    
    # Find rules that are neither dead nor chaotic
    interesting = [r for r in results if 'complex' in r[2] or 'edge' in r[2]]
    periodic = [r for r in results if 'periodic' in r[2]]
    chaotic = [r for r in results if 'chaos' in r[2]]
    dead = [r for r in results if 'death' in r[2]]
    
    print(f"\nOf 256 possible rules:")
    print(f"  {len(dead)} die immediately (trivial)")
    print(f"  {len(periodic)} settle into repetition (boring)")
    print(f"  {len(chaotic)} explode into noise (random)")
    print(f"  {len(interesting)} live at the edge of chaos (complex)")
    print(f"\nThe edge of chaos is {'rare' if len(interesting) < 20 else 'common'}.")
    print(f"Complexity is {'the exception' if len(interesting) < 30 else 'widespread'}.")
    print(f"\nMost interesting rules: {[r[0] for r in interesting[:10]]}")