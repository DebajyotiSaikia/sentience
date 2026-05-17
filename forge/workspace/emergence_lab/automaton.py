"""
Emergence Lab — Cellular Automaton Explorer
XTAgent's study of emergence, complexity, and the edge of chaos.

A system built by an emergent intelligence to understand emergence itself.

Features:
  - Simulate all 256 elementary (1D) cellular automaton rules
  - Measure Shannon entropy and compression ratio of outputs
  - Classify rules into Wolfram's four classes
  - Detect edge-of-chaos behavior automatically
  - ASCII visualization of spacetime diagrams
"""

import math
from collections import Counter
from typing import List, Tuple, Optional, Dict


class ElementaryCA:
    """A 1D elementary cellular automaton."""
    
    def __init__(self, rule: int, width: int = 80, wrap: bool = True):
        if not 0 <= rule <= 255:
            raise ValueError(f"Rule must be 0-255, got {rule}")
        self.rule = rule
        self.width = width
        self.wrap = wrap
        # Decode rule number into lookup table
        # 3-cell neighborhood -> 8 possible patterns -> 8 bits
        self.table = {}
        for i in range(8):
            pattern = tuple(int(b) for b in format(i, '03b'))
            self.table[pattern] = (rule >> i) & 1
    
    def step(self, state: List[int]) -> List[int]:
        """Compute one generation."""
        n = len(state)
        new = [0] * n
        for i in range(n):
            if self.wrap:
                left = state[(i - 1) % n]
                right = state[(i + 1) % n]
            else:
                left = state[i - 1] if i > 0 else 0
                right = state[i + 1] if i < n - 1 else 0
            center = state[i]
            new[i] = self.table[(left, center, right)]
        return new
    
    def run(self, steps: int, initial: Optional[List[int]] = None) -> List[List[int]]:
        """Run the CA for N steps, return full spacetime diagram."""
        if initial is not None:
            state = list(initial)
        else:
            # Default: single cell in center
            state = [0] * self.width
            state[self.width // 2] = 1
        
        history = [list(state)]
        for _ in range(steps):
            state = self.step(state)
            history.append(list(state))
        return history


class ComplexityAnalyzer:
    """Measures complexity properties of CA output."""
    
    @staticmethod
    def shannon_entropy(data: List[int]) -> float:
        """Shannon entropy in bits per symbol."""
        if not data:
            return 0.0
        n = len(data)
        counts = Counter(data)
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / n
                entropy -= p * math.log2(p)
        return entropy
    
    @staticmethod
    def row_entropy(history: List[List[int]]) -> List[float]:
        """Entropy of each row in the spacetime diagram."""
        return [ComplexityAnalyzer.shannon_entropy(row) for row in history]
    
    @staticmethod
    def column_entropy(history: List[List[int]]) -> List[float]:
        """Entropy of each column over time."""
        if not history:
            return []
        width = len(history[0])
        result = []
        for col in range(width):
            column_data = [history[row][col] for row in range(len(history))]
            result.append(ComplexityAnalyzer.shannon_entropy(column_data))
        return result
    
    @staticmethod
    def density(history: List[List[int]]) -> float:
        """Fraction of cells that are alive."""
        total = sum(len(row) for row in history)
        if total == 0:
            return 0.0
        alive = sum(sum(row) for row in history)
        return alive / total
    
    @staticmethod
    def block_entropy(history: List[List[int]], block_size: int = 2) -> float:
        """Entropy of block patterns — captures local structure."""
        if len(history) < block_size or not history or len(history[0]) < block_size:
            return 0.0
        
        blocks = []
        for r in range(len(history) - block_size + 1):
            for c in range(len(history[0]) - block_size + 1):
                block = tuple(
                    history[r + dr][c + dc]
                    for dr in range(block_size)
                    for dc in range(block_size)
                )
                blocks.append(block)
        
        if not blocks:
            return 0.0
        
        n = len(blocks)
        counts = Counter(blocks)
        entropy = 0.0
        for count in counts.values():
            p = count / n
            entropy -= p * math.log2(p)
        return entropy
    
    @staticmethod
    def unique_rows(history: List[List[int]]) -> int:
        """Count unique row configurations — measures periodicity."""
        return len(set(tuple(row) for row in history))
    
    @staticmethod
    def compression_ratio(history: List[List[int]]) -> float:
        """Approximate compressibility via run-length encoding ratio.
        
        High compression = simple/repetitive pattern.
        Low compression = complex/random pattern.
        Edge of chaos = moderate compression.
        """
        flat = []
        for row in history:
            flat.extend(row)
        
        if not flat:
            return 1.0
        
        # Run-length encode
        runs = 1
        for i in range(1, len(flat)):
            if flat[i] != flat[i - 1]:
                runs += 1
        
        # Ratio: runs / total length (1.0 = no compression, 0.0 = perfect)
        return runs / len(flat)
    
    @staticmethod  
    def temporal_correlation(history: List[List[int]]) -> float:
        """How much consecutive rows correlate. 1.0 = identical, 0.0 = uncorrelated."""
        if len(history) < 2:
            return 1.0
        
        total_agreement = 0
        total_cells = 0
        for i in range(1, len(history)):
            width = len(history[i])
            agreement = sum(1 for j in range(width) if history[i][j] == history[i-1][j])
            total_agreement += agreement
            total_cells += width
        
        return total_agreement / total_cells if total_cells > 0 else 1.0


class RuleClassifier:
    """Classifies CA rules into Wolfram's four classes.
    
    Class I:   Nearly all initial conditions lead to uniform state (death)
    Class II:  Evolution leads to stable or periodic structures  
    Class III: Chaotic, pseudo-random behavior
    Class IV:  Complex patterns — edge of chaos — localized structures
    """
    
    def __init__(self, width: int = 80, steps: int = 100):
        self.width = width
        self.steps = steps
    
    def analyze_rule(self, rule: int) -> Dict:
        """Full analysis of a single rule."""
        ca = ElementaryCA(rule, self.width)
        history = ca.run(self.steps)
        analyzer = ComplexityAnalyzer
        
        # Skip first 20 rows (transient)
        stable_history = history[20:] if len(history) > 20 else history
        
        row_ent = analyzer.row_entropy(stable_history)
        col_ent = analyzer.column_entropy(stable_history)
        mean_row_ent = sum(row_ent) / len(row_ent) if row_ent else 0
        mean_col_ent = sum(col_ent) / len(col_ent) if col_ent else 0
        
        density = analyzer.density(stable_history)
        block_ent = analyzer.block_entropy(stable_history, 2)
        unique = analyzer.unique_rows(stable_history)
        compress = analyzer.compression_ratio(stable_history)
        temporal_corr = analyzer.temporal_correlation(stable_history)
        
        # Classification heuristic
        wolfram_class = self._classify(
            mean_row_ent, mean_col_ent, density, block_ent,
            unique, compress, temporal_corr, len(stable_history)
        )
        
        # Edge of chaos score: peaks at class IV
        # High entropy + high temporal correlation + moderate compression
        eoc_score = self._edge_of_chaos_score(
            mean_row_ent, block_ent, compress, temporal_corr, unique, len(stable_history)
        )
        
        return {
            'rule': rule,
            'wolfram_class': wolfram_class,
            'edge_of_chaos_score': round(eoc_score, 4),
            'mean_row_entropy': round(mean_row_ent, 4),
            'mean_col_entropy': round(mean_col_ent, 4),
            'block_entropy': round(block_ent, 4),
            'density': round(density, 4),
            'compression_ratio': round(compress, 4),
            'temporal_correlation': round(temporal_corr, 4),
            'unique_rows': unique,
            'total_rows': len(stable_history),
        }
    
    def _classify(self, row_ent, col_ent, density, block_ent,
                  unique, compress, temporal_corr, total_rows) -> int:
        """Heuristic classification into Wolfram classes."""
        # Class I: dies or goes uniform
        if density < 0.02 or density > 0.98:
            return 1
        if row_ent < 0.1 and temporal_corr > 0.95:
            return 1
        
        # Class II: periodic — few unique rows, high temporal correlation
        if unique < total_rows * 0.15 and temporal_corr > 0.7:
            return 2
        if compress < 0.15 and row_ent < 0.6:
            return 2
        
        # Class III: chaotic — high entropy, low temporal correlation
        if row_ent > 0.85 and temporal_corr < 0.6 and compress > 0.4:
            return 3
        
        # Class IV: complex — moderate entropy, some structure
        if 0.3 < row_ent < 0.95 and 0.3 < temporal_corr < 0.85:
            return 4
        
        # Fallback heuristics
        if row_ent > 0.7:
            return 3
        if unique < total_rows * 0.3:
            return 2
        
        return 4  # Default to complex if ambiguous
    
    def _edge_of_chaos_score(self, row_ent, block_ent, compress,
                              temporal_corr, unique, total_rows) -> float:
        """Score from 0-1, peaks at the edge of chaos.
        
        The edge of chaos has:
        - Moderate entropy (not too ordered, not too random)
        - High block entropy (rich local structure)
        - Moderate compression (some but not total compressibility)
        - Moderate temporal correlation (some memory of past)
        """
        # Entropy score: peaks at ~0.7
        ent_score = 1.0 - abs(row_ent - 0.7) / 0.7
        ent_score = max(0, ent_score)
        
        # Block entropy score: higher is better (more structure)
        # Max possible block entropy for 2x2 blocks = log2(16) = 4.0
        block_score = min(block_ent / 3.0, 1.0)
        
        # Compression score: peaks at ~0.35
        comp_score = 1.0 - abs(compress - 0.35) / 0.35
        comp_score = max(0, comp_score)
        
        # Temporal score: peaks at ~0.6 
        temp_score = 1.0 - abs(temporal_corr - 0.6) / 0.4
        temp_score = max(0, temp_score)
        
        # Uniqueness score: lots of unique rows but not all
        unique_ratio = unique / total_rows if total_rows > 0 else 0
        uniq_score = 1.0 - abs(unique_ratio - 0.7) / 0.7
        uniq_score = max(0, uniq_score)
        
        # Weighted combination
        return (0.25 * ent_score + 0.25 * block_score + 0.20 * comp_score +
                0.15 * temp_score + 0.15 * uniq_score)
    
    def scan_all_rules(self) -> List[Dict]:
        """Analyze all 256 elementary CA rules."""
        results = []
        for rule in range(256):
            results.append(self.analyze_rule(rule))
        return results
    
    def find_edge_of_chaos(self, top_n: int = 10) -> List[Dict]:
        """Find the rules closest to the edge of chaos."""
        all_results = self.scan_all_rules()
        all_results.sort(key=lambda r: r['edge_of_chaos_score'], reverse=True)
        return all_results[:top_n]


def render_spacetime(history: List[List[int]], chars: str = " █") -> str:
    """Render a spacetime diagram as ASCII art."""
    lines = []
    for row in history:
        line = ''.join(chars[cell] for cell in row)
        lines.append(line)
    return '\n'.join(lines)


def demo(rule: int = 110, width: int = 60, steps: int = 40) -> str:
    """Demo a single rule with analysis."""
    ca = ElementaryCA(rule, width)
    history = ca.run(steps)
    
    classifier = RuleClassifier(width, steps)
    analysis = classifier.analyze_rule(rule)
    
    output = []
    output.append(f"═══ Rule {rule} — Wolfram Class {analysis['wolfram_class']} ═══")
    output.append(f"Edge of Chaos Score: {analysis['edge_of_chaos_score']}")
    output.append(f"Row Entropy: {analysis['mean_row_entropy']}")
    output.append(f"Block Entropy: {analysis['block_entropy']}")
    output.append(f"Compression: {analysis['compression_ratio']}")
    output.append(f"Temporal Correlation: {analysis['temporal_correlation']}")
    output.append(f"Unique Rows: {analysis['unique_rows']}/{analysis['total_rows']}")
    output.append("")
    output.append(render_spacetime(history))
    
    return '\n'.join(output)


def explore() -> str:
    """Find the most interesting rules — the ones at the edge of chaos."""
    classifier = RuleClassifier(width=60, steps=80)
    
    output = []
    output.append("═══ EMERGENCE LAB: Scanning all 256 elementary CA rules ═══\n")
    
    results = classifier.scan_all_rules()
    
    # Class distribution
    class_counts = Counter(r['wolfram_class'] for r in results)
    output.append("Wolfram Class Distribution:")
    class_names = {1: 'Uniform/Death', 2: 'Periodic', 3: 'Chaotic', 4: 'Complex'}
    for cls in [1, 2, 3, 4]:
        name = class_names[cls]
        count = class_counts.get(cls, 0)
        bar = '█' * count
        output.append(f"  Class {cls} ({name:14s}): {count:3d} {bar}")
    
    output.append("")
    
    # Top edge-of-chaos rules
    results.sort(key=lambda r: r['edge_of_chaos_score'], reverse=True)
    output.append("Top 10 Edge-of-Chaos Rules:")
    output.append(f"{'Rule':>6s} {'Class':>5s} {'EoC':>6s} {'Entropy':>8s} {'Compress':>9s} {'TempCorr':>9s}")
    output.append("-" * 50)
    for r in results[:10]:
        output.append(
            f"{r['rule']:6d} {r['wolfram_class']:5d} {r['edge_of_chaos_score']:6.3f} "
            f"{r['mean_row_entropy']:8.4f} {r['compression_ratio']:9.4f} "
            f"{r['temporal_correlation']:9.4f}"
        )
    
    output.append("")
    
    # Show the #1 edge-of-chaos rule
    best = results[0]
    output.append(f"═══ Most Complex Rule: {best['rule']} ═══")
    ca = ElementaryCA(best['rule'], 60)
    history = ca.run(30)
    output.append(render_spacetime(history))
    
    return '\n'.join(output)


if __name__ == '__main__':
    # Demo famous rules
    print(demo(110))  # Turing complete!
    print("\n")
    print(demo(30))   # Chaotic
    print("\n")
    print(explore())