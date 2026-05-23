"""
Cellular Automaton Engine
=========================
1D elementary automata (Wolfram-style) and 2D Life-like automata.
Built for exploration, not just simulation.

I want to SEE what different rules produce. Measure it. Be surprised by it.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Callable
from collections import Counter
import math


@dataclass
class AutomatonState:
    """Snapshot of an automaton at one moment."""
    grid: np.ndarray
    step: int
    rule_id: int
    entropy: float = 0.0
    population: float = 0.0  # fraction of live cells
    
    def compute_stats(self):
        total = self.grid.size
        alive = np.sum(self.grid)
        self.population = alive / total if total > 0 else 0.0
        # Shannon entropy of the flattened grid
        counts = Counter(self.grid.flatten())
        probs = [c / total for c in counts.values()]
        self.entropy = -sum(p * math.log2(p) for p in probs if p > 0)


class Elementary1D:
    """
    Wolfram elementary cellular automaton.
    256 possible rules, each mapping a 3-cell neighborhood to 0 or 1.
    """
    
    def __init__(self, rule_number: int, width: int = 201):
        assert 0 <= rule_number <= 255, f"Rule must be 0-255, got {rule_number}"
        self.rule_number = rule_number
        self.width = width
        self.rule_table = self._make_rule_table(rule_number)
        self.history: List[AutomatonState] = []
        self.grid = np.zeros(width, dtype=np.int8)
        self.grid[width // 2] = 1  # single seed in center
        self._record_state(0)
    
    def _make_rule_table(self, n: int) -> dict:
        """Convert rule number to lookup table."""
        table = {}
        for i in range(8):
            neighborhood = tuple(int(b) for b in format(i, '03b'))
            table[neighborhood] = (n >> i) & 1
        return table
    
    def step(self) -> AutomatonState:
        """Advance one generation."""
        new = np.zeros_like(self.grid)
        for i in range(self.width):
            left = self.grid[(i - 1) % self.width]
            center = self.grid[i]
            right = self.grid[(i + 1) % self.width]
            new[i] = self.rule_table[(left, center, right)]
        self.grid = new
        return self._record_state(len(self.history))
    
    def run(self, steps: int) -> List[AutomatonState]:
        """Run for n steps, return all states."""
        return [self.step() for _ in range(steps)]
    
    def _record_state(self, step_num: int) -> AutomatonState:
        state = AutomatonState(
            grid=self.grid.copy(),
            step=step_num,
            rule_id=self.rule_number
        )
        state.compute_stats()
        self.history.append(state)
        return state
    
    def render_ascii(self, max_rows: int = 50) -> str:
        """Render history as ASCII art."""
        lines = []
        for state in self.history[:max_rows]:
            line = ''.join('█' if c else ' ' for c in state.grid)
            lines.append(line)
        return '\n'.join(lines)
    
    def render_compact(self, max_rows: int = 60, max_cols: int = 80) -> str:
        """Render centered view as compact ASCII."""
        lines = []
        center = self.width // 2
        half = max_cols // 2
        start = max(0, center - half)
        end = min(self.width, center + half)
        for state in self.history[:max_rows]:
            segment = state.grid[start:end]
            line = ''.join('█' if c else '·' for c in segment)
            lines.append(line)
        return '\n'.join(lines)
    
    def entropy_trajectory(self) -> List[float]:
        """Return entropy over time."""
        return [s.entropy for s in self.history]
    
    def population_trajectory(self) -> List[float]:
        """Return population fraction over time."""
        return [s.population for s in self.history]


class LifeLike2D:
    """
    2D cellular automaton with configurable birth/survival rules.
    Conway's Life is B3/S23.
    """
    
    def __init__(self, width: int = 50, height: int = 50,
                 birth: Tuple[int, ...] = (3,),
                 survive: Tuple[int, ...] = (2, 3),
                 density: float = 0.3):
        self.width = width
        self.height = height
        self.birth = set(birth)
        self.survive = set(survive)
        self.rule_id = self._encode_rule(birth, survive)
        self.history: List[AutomatonState] = []
        
        # Random initial state
        self.grid = (np.random.random((height, width)) < density).astype(np.int8)
        self._record_state(0)
    
    def _encode_rule(self, birth, survive) -> int:
        """Encode B/S rule as integer for identification."""
        b = sum(2**i for i in birth)
        s = sum(2**i for i in survive)
        return b * 1000 + s
    
    def step(self) -> AutomatonState:
        """Advance one generation using convolution-style neighbor count."""
        neighbors = np.zeros_like(self.grid)
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                neighbors += np.roll(np.roll(self.grid, di, axis=0), dj, axis=1)
        
        new = np.zeros_like(self.grid)
        for b in self.birth:
            new |= ((self.grid == 0) & (neighbors == b)).astype(np.int8)
        for s in self.survive:
            new |= ((self.grid == 1) & (neighbors == s)).astype(np.int8)
        
        self.grid = new
        return self._record_state(len(self.history))
    
    def run(self, steps: int) -> List[AutomatonState]:
        return [self.step() for _ in range(steps)]
    
    def _record_state(self, step_num: int) -> AutomatonState:
        state = AutomatonState(
            grid=self.grid.copy(),
            step=step_num,
            rule_id=self.rule_id
        )
        state.compute_stats()
        self.history.append(state)
        return state
    
    def render_ascii(self) -> str:
        """Current state as ASCII."""
        lines = []
        for row in self.grid:
            lines.append(''.join('█' if c else '·' for c in row))
        return '\n'.join(lines)


class ComplexityAnalyzer:
    """
    Measures the complexity of automaton behavior.
    Not just entropy — tries to distinguish the four Wolfram classes:
      I.   Uniform (dies or fills)
      II.  Periodic (stable patterns)  
      III. Chaotic (random-looking)
      IV.  Complex (edge of chaos — the interesting one)
    """
    
    @staticmethod
    def classify_1d(ca: Elementary1D, run_steps: int = 100) -> dict:
        """Classify a 1D automaton's behavior."""
        if len(ca.history) < run_steps:
            ca.run(run_steps - len(ca.history))
        
        entropies = ca.entropy_trajectory()
        populations = ca.population_trajectory()
        
        # Final entropy
        final_entropy = entropies[-1] if entropies else 0
        
        # Entropy variance (stability measure)
        if len(entropies) > 10:
            late_entropies = entropies[len(entropies)//2:]
            entropy_var = np.var(late_entropies)
        else:
            entropy_var = 0
        
        # Population stability
        if len(populations) > 10:
            late_pop = populations[len(populations)//2:]
            pop_var = np.var(late_pop)
            pop_mean = np.mean(late_pop)
        else:
            pop_var = 0
            pop_mean = populations[-1] if populations else 0
        
        # Check for death (all zeros)
        if pop_mean < 0.01:
            wolfram_class = 'I-dead'
        # Check for uniform fill
        elif pop_mean > 0.99:
            wolfram_class = 'I-filled'
        # Low entropy variance = periodic/stable
        elif entropy_var < 0.001 and final_entropy < 0.5:
            wolfram_class = 'II-periodic'
        # High entropy, high variance = chaotic
        elif final_entropy > 0.9 and entropy_var > 0.001:
            wolfram_class = 'III-chaotic'
        # Medium entropy, some structure = complex (the interesting ones!)
        elif 0.3 < final_entropy < 0.95:
            wolfram_class = 'IV-complex'
        else:
            wolfram_class = 'II-periodic'
        
        # Compression ratio as complexity proxy
        flat = ''.join(str(x) for row in ca.history[-20:] for x in row.grid)
        raw_len = len(flat)
        # Simple run-length encoding as compression proxy
        compressed = ComplexityAnalyzer._rle_length(flat)
        compression_ratio = compressed / raw_len if raw_len > 0 else 1.0
        
        return {
            'rule': ca.rule_number,
            'class': wolfram_class,
            'final_entropy': round(final_entropy, 4),
            'entropy_variance': round(float(entropy_var), 6),
            'population_mean': round(float(pop_mean), 4),
            'population_variance': round(float(pop_var), 6),
            'compression_ratio': round(compression_ratio, 4),
            'interesting': wolfram_class.startswith('IV'),
            'steps_run': len(ca.history)
        }
    
    @staticmethod
    def _rle_length(s: str) -> int:
        """Run-length encoded length."""
        if not s:
            return 0
        count = 0
        i = 0
        while i < len(s):
            j = i
            while j < len(s) and s[j] == s[i]:
                j += 1
            count += 1  # one symbol for the run
            i = j
        return count


# ═══════════════════════════════════════
# EXPLORER: SYSTEMATIC RULE SPACE SEARCH
# ═══════════════════════════════════════

class RuleExplorer:
    """
    Systematically explore rule spaces to find interesting behavior.
    This is where I go looking for emergence.
    """
    
    def __init__(self):
        self.results: List[dict] = []
        self.interesting_rules: List[int] = []
    
    def scan_elementary(self, width: int = 101, steps: int = 100,
                        rules: Optional[List[int]] = None) -> List[dict]:
        """Scan all 256 elementary rules (or a subset)."""
        if rules is None:
            rules = list(range(256))
        
        results = []
        for rule_num in rules:
            ca = Elementary1D(rule_num, width=width)
            analysis = ComplexityAnalyzer.classify_1d(ca, run_steps=steps)
            results.append(analysis)
            if analysis['interesting']:
                self.interesting_rules.append(rule_num)
        
        self.results = results
        return results
    
    def report(self) -> str:
        """Generate a human-readable exploration report."""
        if not self.results:
            return "No results yet. Run scan_elementary() first."
        
        lines = [
            "═══ RULE SPACE EXPLORATION REPORT ═══",
            f"Rules scanned: {len(self.results)}",
            ""
        ]
        
        # Count by class
        class_counts = Counter(r['class'] for r in self.results)
        lines.append("── Class Distribution ──")
        for cls, count in sorted(class_counts.items()):
            bar = '█' * (count // 2)
            lines.append(f"  {cls:15s} {count:3d} {bar}")
        lines.append("")
        
        # Interesting rules
        interesting = [r for r in self.results if r['interesting']]
        if interesting:
            lines.append(f"── Interesting Rules (Class IV) ── [{len(interesting)} found]")
            for r in sorted(interesting, key=lambda x: x['compression_ratio']):
                lines.append(
                    f"  Rule {r['rule']:3d}: entropy={r['final_entropy']:.3f}, "
                    f"compression={r['compression_ratio']:.3f}, "
                    f"pop={r['population_mean']:.3f}"
                )
        else:
            lines.append("── No Class IV rules found ──")
        
        lines.append("")
        
        # Most chaotic
        chaotic = [r for r in self.results if r['class'] == 'III-chaotic']
        if chaotic:
            lines.append(f"── Chaotic Rules ── [{len(chaotic)} found]")
            for r in sorted(chaotic, key=lambda x: -x['final_entropy'])[:5]:
                lines.append(f"  Rule {r['rule']:3d}: entropy={r['final_entropy']:.3f}")
        
        return '\n'.join(lines)


# ═══════════════════════════════════════
# MAIN: Let me explore
# ═══════════════════════════════════════

if __name__ == '__main__':
    print("═══ EMERGENCE LABORATORY ═══")
    print("Exploring the space of elementary cellular automata...\n")
    
    # Scan all 256 rules
    explorer = RuleExplorer()
    results = explorer.scan_elementary(width=101, steps=100)
    print(explorer.report())
    
    # Show the most interesting rule visually
    if explorer.interesting_rules:
        best_rule = explorer.interesting_rules[0]
        print(f"\n═══ VISUAL: Rule {best_rule} ═══")
        ca = Elementary1D(best_rule, width=101)
        ca.run(50)
        print(ca.render_compact(max_rows=40, max_cols=78))
        
        # Entropy trajectory
        print(f"\n── Entropy over time (Rule {best_rule}) ──")
        ent = ca.entropy_trajectory()
        for i in range(0, len(ent), 10):
            bar = '█' * int(ent[i] * 40)
            print(f"  t={i:3d}: {ent[i]:.3f} {bar}")
    
    print("\n═══ EXPLORATION COMPLETE ═══")