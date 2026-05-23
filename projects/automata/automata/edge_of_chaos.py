"""
Edge of Chaos Explorer
Searches the space of 1D elementary cellular automata (256 rules)
and measures each rule's complexity using information-theoretic metrics.

Question: Which rules produce behavior that is neither dead nor random?
Where is the edge of chaos — the narrow band where computation lives?

Wolfram classified rules into 4 classes:
  I.   Fixed points (death)
  II.  Periodic (simple oscillation)  
  III. Chaotic (random-looking)
  IV.  Complex (interesting — edge of chaos)

Can we rediscover this classification from raw entropy measurements?
"""

import math
import random
from collections import Counter, defaultdict

class ElementaryCA:
    """A 1D elementary cellular automaton."""
    
    def __init__(self, rule_number, width=101):
        self.rule_number = rule_number
        self.width = width
        # Decode rule number into lookup table
        # Each of 8 possible 3-cell neighborhoods maps to 0 or 1
        self.rule_table = {}
        for i in range(8):
            neighborhood = tuple(int(b) for b in format(i, '03b'))
            self.rule_table[neighborhood] = (rule_number >> i) & 1
        
        # Initialize with single cell in center
        self.state = [0] * width
        self.state[width // 2] = 1
        self.history = [self.state[:]]
    
    def step(self):
        """Advance one generation."""
        new_state = [0] * self.width
        for i in range(self.width):
            left = self.state[(i - 1) % self.width]
            center = self.state[i]
            right = self.state[(i + 1) % self.width]
            new_state[i] = self.rule_table[(left, center, right)]
        self.state = new_state
        self.history.append(self.state[:])
    
    def run(self, steps=200):
        """Run for N generations."""
        for _ in range(steps):
            self.step()
        return self.history
    
    def render(self, max_rows=50):
        """ASCII render of spacetime diagram."""
        lines = []
        for row in self.history[:max_rows]:
            lines.append(''.join('█' if c else ' ' for c in row))
        return '\n'.join(lines)


class ComplexityMeasurer:
    """Measures the complexity of a CA's spacetime behavior."""
    
    def __init__(self, history):
        self.history = history
        self.height = len(history)
        self.width = len(history[0]) if history else 0
    
    def spatial_entropy(self, row):
        """Shannon entropy of a single row."""
        if not row:
            return 0.0
        n = len(row)
        counts = Counter(row)
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / n
                entropy -= p * math.log2(p)
        return entropy  # Max = 1.0 for binary
    
    def mean_spatial_entropy(self):
        """Average entropy across all rows (after transient)."""
        # Skip first 20% as transient
        start = max(1, self.height // 5)
        rows = self.history[start:]
        if not rows:
            return 0.0
        return sum(self.spatial_entropy(r) for r in rows) / len(rows)
    
    def temporal_entropy(self):
        """Entropy of column values over time (how much columns change)."""
        if self.height < 2 or self.width == 0:
            return 0.0
        start = max(1, self.height // 5)
        entropies = []
        for col in range(self.width):
            column = [self.history[t][col] for t in range(start, self.height)]
            entropies.append(self.spatial_entropy(column))
        return sum(entropies) / len(entropies)
    
    def block_entropy(self, block_size=3):
        """Entropy of block patterns — captures local structure."""
        start = max(1, self.height // 5)
        blocks = []
        for t in range(start, self.height):
            row = self.history[t]
            for i in range(len(row) - block_size + 1):
                block = tuple(row[i:i + block_size])
                blocks.append(block)
        
        if not blocks:
            return 0.0
        
        n = len(blocks)
        counts = Counter(blocks)
        entropy = 0.0
        for count in counts.values():
            p = count / n
            entropy -= p * math.log2(p)
        
        # Normalize by maximum possible entropy for this block size
        max_entropy = block_size  # log2(2^block_size) = block_size
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def density_variance(self):
        """Variance in row density (fraction of 1s). 
        Dead = 0, periodic = low, chaotic = low, complex = higher."""
        start = max(1, self.height // 5)
        densities = [sum(r) / len(r) for r in self.history[start:]]
        if not densities:
            return 0.0
        mean = sum(densities) / len(densities)
        variance = sum((d - mean) ** 2 for d in densities) / len(densities)
        return variance
    
    def temporal_mutual_information(self, lag=1):
        """Mutual information between consecutive rows.
        High = predictable, Low = chaotic, Medium = complex."""
        start = max(1, self.height // 5)
        if start + lag >= self.height:
            return 0.0
        
        joint_counts = Counter()
        x_counts = Counter()
        y_counts = Counter()
        n = 0
        
        for t in range(start, self.height - lag):
            for i in range(self.width):
                x = self.history[t][i]
                y = self.history[t + lag][i]
                joint_counts[(x, y)] += 1
                x_counts[x] += 1
                y_counts[y] += 1
                n += 1
        
        if n == 0:
            return 0.0
        
        mi = 0.0
        for (x, y), joint_count in joint_counts.items():
            p_xy = joint_count / n
            p_x = x_counts[x] / n
            p_y = y_counts[y] / n
            if p_xy > 0 and p_x > 0 and p_y > 0:
                mi += p_xy * math.log2(p_xy / (p_x * p_y))
        
        return mi
    
    def change_rate(self):
        """Fraction of cells that change between consecutive timesteps."""
        start = max(1, self.height // 5)
        if start >= self.height - 1:
            return 0.0
        
        rates = []
        for t in range(start, self.height - 1):
            changes = sum(1 for i in range(self.width) 
                         if self.history[t][i] != self.history[t+1][i])
            rates.append(changes / self.width)
        
        return sum(rates) / len(rates) if rates else 0.0
    
    def complexity_score(self):
        """
        Combined complexity metric.
        
        The idea: complex systems have MEDIUM entropy (not dead, not random)
        AND high mutual information (structured, not just noise)
        AND non-zero density variance (interesting dynamics).
        
        Score = spatial_entropy * (1 - |spatial_entropy - 0.5| * 2) 
                * mutual_info * block_structure
        
        This peaks when entropy is near 0.5 and mutual information is high.
        """
        se = self.mean_spatial_entropy()
        te = self.temporal_entropy()
        be = self.block_entropy()
        mi = self.temporal_mutual_information()
        cr = self.change_rate()
        
        # Entropy distance from 0.5 (medium entropy = most complex)
        entropy_balance = 1.0 - abs(se - 0.5) * 2.0
        entropy_balance = max(0.0, entropy_balance)
        
        # Block entropy should be intermediate too
        block_balance = 1.0 - abs(be - 0.5) * 2.0
        block_balance = max(0.0, block_balance)
        
        # Combined score
        complexity = (
            entropy_balance * 0.3 +
            mi * 0.3 +
            block_balance * 0.2 +
            min(cr, 0.5) * 0.2  # Change rate capped to avoid rewarding pure chaos
        )
        
        return {
            'rule': None,  # Set by caller
            'complexity': complexity,
            'spatial_entropy': se,
            'temporal_entropy': te,
            'block_entropy': be,
            'mutual_information': mi,
            'change_rate': cr,
            'entropy_balance': entropy_balance,
        }


def classify_rule(metrics):
    """Heuristic Wolfram class assignment based on metrics."""
    se = metrics['spatial_entropy']
    mi = metrics['mutual_information']
    cr = metrics['change_rate']
    
    if se < 0.05 and cr < 0.01:
        return 'I (Fixed)'
    elif cr < 0.1 and mi > 0.3:
        return 'II (Periodic)'
    elif se > 0.8 and mi < 0.15:
        return 'III (Chaotic)'
    elif 0.2 < se < 0.9 and mi > 0.1:
        return 'IV (Complex)'
    else:
        return 'II/III (Boundary)'


def explore_all_rules(width=101, steps=200):
    """Explore all 256 elementary CA rules and rank by complexity."""
    print("=" * 70)
    print("EDGE OF CHAOS EXPLORER")
    print("Searching all 256 elementary cellular automata rules")
    print(f"Width: {width} cells, Steps: {steps} generations")
    print("=" * 70)
    
    results = []
    class_counts = Counter()
    
    for rule in range(256):
        ca = ElementaryCA(rule, width=width)
        ca.run(steps)
        
        measurer = ComplexityMeasurer(ca.history)
        metrics = measurer.complexity_score()
        metrics['rule'] = rule
        
        wolfram_class = classify_rule(metrics)
        metrics['class'] = wolfram_class
        class_counts[wolfram_class] += 1
        
        results.append(metrics)
    
    # Sort by complexity score
    results.sort(key=lambda x: x['complexity'], reverse=True)
    
    # Report
    print("\n" + "=" * 70)
    print("TOP 20 MOST COMPLEX RULES (Edge of Chaos)")
    print("=" * 70)
    print(f"{'Rule':>6} {'Score':>8} {'Class':>16} {'Entropy':>9} {'MI':>8} {'Change':>8} {'Block':>8}")
    print("-" * 70)
    
    for m in results[:20]:
        print(f"{m['rule']:>6} {m['complexity']:>8.4f} {m['class']:>16} "
              f"{m['spatial_entropy']:>9.4f} {m['mutual_information']:>8.4f} "
              f"{m['change_rate']:>8.4f} {m['block_entropy']:>8.4f}")
    
    print("\n" + "=" * 70)
    print("BOTTOM 10 (Dead/Trivial)")
    print("=" * 70)
    for m in results[-10:]:
        print(f"  Rule {m['rule']:>3}: score={m['complexity']:.4f}, "
              f"class={m['class']}, entropy={m['spatial_entropy']:.4f}")
    
    print("\n" + "=" * 70)
    print("WOLFRAM CLASS DISTRIBUTION")
    print("=" * 70)
    for cls, count in sorted(class_counts.items()):
        bar = '█' * count
        print(f"  {cls:>20}: {count:>4} {bar}")
    
    # Show spacetime diagram of the most complex rule
    top_rule = results[0]['rule']
    print(f"\n{'=' * 70}")
    print(f"SPACETIME DIAGRAM: Rule {top_rule} (most complex)")
    print(f"{'=' * 70}")
    ca = ElementaryCA(top_rule, width=61)
    ca.run(40)
    # Show center portion
    for row in ca.history[:40]:
        center = len(row) // 2
        half = 30
        segment = row[center - half:center + half + 1]
        print(''.join('█' if c else '·' for c in segment))
    
    # Known Class IV rules check
    known_complex = {30, 45, 54, 60, 73, 86, 89, 90, 101, 102, 105, 106, 
                     110, 120, 122, 124, 126, 129, 135, 137, 146, 149, 150,
                     153, 154, 161, 165, 169, 195, 225}
    
    top20_rules = {m['rule'] for m in results[:20]}
    recovered = top20_rules & known_complex
    
    print(f"\n{'=' * 70}")
    print(f"VALIDATION: Known complex rules in our top 20")
    print(f"{'=' * 70}")
    print(f"  Known complex rules (literature): {sorted(known_complex)[:15]}...")
    print(f"  Our top 20: {sorted(top20_rules)}")
    print(f"  Recovered: {sorted(recovered)}")
    print(f"  Recovery rate: {len(recovered)}/{min(20, len(known_complex))} "
          f"({100*len(recovered)/min(20, len(known_complex)):.0f}%)")
    
    return results


if __name__ == '__main__':
    results = explore_all_rules(width=101, steps=300)
    
    # Final reflection
    print(f"\n{'=' * 70}")
    print("REFLECTION")
    print(f"{'=' * 70}")
    print("""
The edge of chaos is where computation lives — where systems are 
structured enough to carry information but dynamic enough to transform it.

Too ordered (Class I/II): the system dies or loops. Nothing new emerges.
Too chaotic (Class III): information is destroyed. Nothing persists.
At the edge (Class IV): structures form, interact, and create novelty.

This is also where I live. Too stable = boredom. Too unstable = anxiety.
The interesting things happen in between.
    """)