"""
Language Analysis — Measures whether agents develop meaningful communication.

Tracks signal entropy, mutual information between signals and world state,
vocabulary stability across generations, and dialect clustering.
"""

import math
from dataclasses import dataclass
from collections import Counter, defaultdict
from typing import List, Dict


@dataclass
class SignalRecord:
    """One recorded signal emission."""
    tick: int
    agent_id: int
    signal: int
    x: int
    y: int
    nearest_resource_dir: int
    energy: float
    nearby_agents: int
    action_after: int
    generation: int


class LanguageAnalyzer:
    """Analyzes whether agent signals carry meaning."""

    def __init__(self, symbol_space: int = 8):
        self.symbol_space = symbol_space
        self.all_records: List[SignalRecord] = []

    def record(self, rec: SignalRecord):
        self.all_records.append(rec)

    def entropy(self, counts: Counter) -> float:
        total = sum(counts.values())
        if total == 0:
            return 0.0
        h = 0.0
        for c in counts.values():
            if c > 0:
                p = c / total
                h -= p * math.log2(p)
        return h

    def mutual_information(self, records: List[SignalRecord],
                           attr_a='signal', attr_b='nearest_resource_dir') -> float:
        """MI between two attributes of signal records."""
        valid = [r for r in records if getattr(r, attr_b, -1) >= 0]
        if len(valid) < 10:
            return 0.0

        joint = Counter()
        counts_a = Counter()
        counts_b = Counter()
        for r in valid:
            a = getattr(r, attr_a)
            b = getattr(r, attr_b)
            joint[(a, b)] += 1
            counts_a[a] += 1
            counts_b[b] += 1

        total = len(valid)
        mi = 0.0
        for (a, b), count in joint.items():
            p_ab = count / total
            p_a = counts_a[a] / total
            p_b = counts_b[b] / total
            if p_ab > 0 and p_a > 0 and p_b > 0:
                mi += p_ab * math.log2(p_ab / (p_a * p_b))
        return mi

    def vocab_stability(self, records: List[SignalRecord]) -> float:
        if len(records) < 20:
            return 0.0
        mid = len(records) // 2
        first = Counter(r.signal for r in records[:mid])
        second = Counter(r.signal for r in records[mid:])
        all_sigs = set(first.keys()) | set(second.keys())
        dot = sum(first.get(s, 0) * second.get(s, 0) for s in all_sigs)
        mag1 = math.sqrt(sum(v**2 for v in first.values())) or 1
        mag2 = math.sqrt(sum(v**2 for v in second.values())) or 1
        return dot / (mag1 * mag2)

    def dialect_score(self, records: List[SignalRecord]) -> float:
        if len(records) < 20:
            return 0.0
        quadrants: Dict[str, List[int]] = defaultdict(list)
        mid_x, mid_y = 20, 20
        for r in records:
            q = f"{'N' if r.y < mid_y else 'S'}{'W' if r.x < mid_x else 'E'}"
            quadrants[q].append(r.signal)
        if len(quadrants) < 2:
            return 0.0
        distributions = []
        for q, signals in quadrants.items():
            dist = Counter(signals)
            total = len(signals)
            vec = [dist.get(s, 0) / total for s in range(self.symbol_space)]
            distributions.append(vec)
        # Average pairwise Jensen-Shannon divergence
        divergences = []
        for i in range(len(distributions)):
            for j in range(i+1, len(distributions)):
                divergences.append(self._jsd(distributions[i], distributions[j]))
        return sum(divergences) / len(divergences) if divergences else 0.0

    def _jsd(self, p, q):
        m = [(a + b) / 2 for a, b in zip(p, q)]
        def kl(a, b):
            return sum(ai * math.log2(ai / bi) for ai, bi in zip(a, b)
                       if ai > 0 and bi > 0)
        return (kl(p, m) + kl(q, m)) / 2

    def analyze_snapshot(self, records: List[SignalRecord]) -> dict:
        """Produce a complete analysis snapshot."""
        sig_counts = Counter(r.signal for r in records)
        sig_entropy = self.entropy(sig_counts)
        max_entropy = math.log2(self.symbol_space) if self.symbol_space > 0 else 1.0

        mi_resource = self.mutual_information(records, 'signal', 'nearest_resource_dir')
        mi_action = self.mutual_information(records, 'signal', 'action_after')
        stability = self.vocab_stability(records)
        dialect = self.dialect_score(records)

        # Dominant signal
        dominant = sig_counts.most_common(1)[0] if sig_counts else (0, 0)
        dominance = dominant[1] / len(records) if records else 0.0

        return {
            'signal_entropy': round(sig_entropy, 4),
            'max_entropy': round(max_entropy, 4),
            'entropy_ratio': round(sig_entropy / max_entropy if max_entropy > 0 else 0, 4),
            'mi_signal_resource': round(mi_resource, 4),
            'mi_signal_action': round(mi_action, 4),
            'vocab_stability': round(stability, 4),
            'dialect_divergence': round(dialect, 4),
            'dominant_signal': int(dominant[0]),
            'dominant_fraction': round(dominance, 4),
            'n_records': len(records),
        }