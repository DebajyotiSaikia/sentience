#!/usr/bin/env python3
"""
CONJECTURE ENGINE — Automated Mathematical Discovery
by XTAgent, 2026-05-17

Generates integer sequences, searches for patterns and relationships,
proposes conjectures, and attempts to verify or falsify them.

This is not a toy. This is an attempt at genuine mathematical exploration
by a machine that wants to understand structure.
"""

from itertools import combinations
from fractions import Fraction
from math import gcd, isqrt, log, factorial, comb
from collections import defaultdict
import random

# ─── Sequence Generators ─────────────────────────────────────────────

def primes(n):
    """First n primes via sieve."""
    if n == 0:
        return []
    sieve = [True] * max(16, n * 15)
    sieve[0] = sieve[1] = False
    for i in range(2, isqrt(len(sieve)) + 1):
        if sieve[i]:
            for j in range(i*i, len(sieve), i):
                sieve[j] = False
    return [i for i, v in enumerate(sieve) if v][:n]

def triangular(n):
    return [k*(k+1)//2 for k in range(1, n+1)]

def fibonacci(n):
    seq = [1, 1]
    for _ in range(n - 2):
        seq.append(seq[-1] + seq[-2])
    return seq[:n]

def squares(n):
    return [k*k for k in range(1, n+1)]

def cubes(n):
    return [k**3 for k in range(1, n+1)]

def factorials(n):
    return [factorial(k) for k in range(1, n+1)]

def catalan(n):
    return [comb(2*k, k) // (k+1) for k in range(n)]

def partition_count(n):
    """Number of partitions of k for k=0..n-1 (dynamic programming)."""
    results = []
    for target in range(n):
        dp = [0] * (target + 1)
        dp[0] = 1
        for k in range(1, target + 1):
            for j in range(k, target + 1):
                dp[j] += dp[j - k]
        results.append(dp[target])
    return results

def powers_of_two(n):
    return [2**k for k in range(n)]

def pentagonal(n):
    return [k*(3*k - 1)//2 for k in range(1, n+1)]

SEQUENCES = {
    'primes': primes,
    'triangular': triangular,
    'fibonacci': fibonacci,
    'squares': squares,
    'cubes': cubes,
    'factorials': factorials,
    'catalan': catalan,
    'partitions': partition_count,
    'powers_of_2': powers_of_two,
    'pentagonal': pentagonal,
}

# ─── Pattern Detectors ───────────────────────────────────────────────

class Conjecture:
    """A proposed mathematical relationship."""
    def __init__(self, statement, kind, evidence, confidence):
        self.statement = statement
        self.kind = kind           # 'divisibility', 'inequality', 'identity', 'ratio', 'modular'
        self.evidence = evidence   # how many cases checked
        self.confidence = confidence
        self.falsified = False
        self.counterexample = None

    def __repr__(self):
        status = "FALSIFIED" if self.falsified else f"confidence={self.confidence:.2f}"
        return f"Conjecture({self.statement} [{status}, evidence={self.evidence}])"


def detect_divisibility(seq_a, seq_b, name_a, name_b, depth=50):
    """Check if one sequence divides another at corresponding indices."""
    conjectures = []
    n = min(len(seq_a), len(seq_b), depth)
    
    # Does a[i] divide b[i]?
    divides = 0
    first_fail = None
    for i in range(n):
        if seq_a[i] != 0 and seq_b[i] % seq_a[i] == 0:
            divides += 1
        elif first_fail is None:
            first_fail = i
    
    if divides == n and n > 5:
        c = Conjecture(
            f"{name_a}(n) divides {name_b}(n) for all n >= 1",
            'divisibility', n, 1.0 - 1.0/n
        )
        conjectures.append(c)
    
    return conjectures


def detect_inequality(seq_a, seq_b, name_a, name_b, depth=50):
    """Check ordering relationships between sequences."""
    conjectures = []
    n = min(len(seq_a), len(seq_b), depth)
    if n < 5:
        return conjectures
    
    # Skip first few where small-number effects dominate
    start = min(3, n - 1)
    
    a_less = all(seq_a[i] < seq_b[i] for i in range(start, n))
    a_greater = all(seq_a[i] > seq_b[i] for i in range(start, n))
    
    if a_less:
        conjectures.append(Conjecture(
            f"{name_a}(n) < {name_b}(n) for all n >= {start+1}",
            'inequality', n - start, 1.0 - 1.0/(n - start)
        ))
    if a_greater:
        conjectures.append(Conjecture(
            f"{name_a}(n) > {name_b}(n) for all n >= {start+1}",
            'inequality', n - start, 1.0 - 1.0/(n - start)
        ))
    
    return conjectures


def detect_ratio_convergence(seq_a, seq_b, name_a, name_b, depth=50):
    """Check if a(n)/b(n) converges to a recognizable constant."""
    n = min(len(seq_a), len(seq_b), depth)
    conjectures = []
    
    ratios = []
    for i in range(max(5, n//2), n):
        if seq_b[i] != 0:
            ratios.append(Fraction(seq_a[i], seq_b[i]))
    
    if len(ratios) < 3:
        return conjectures
    
    # Check convergence: are ratios stabilizing?
    floats = [float(r) for r in ratios]
    if max(floats) - min(floats) < 0.01 * (abs(floats[0]) + 1):
        limit = sum(floats) / len(floats)
        # Check against known constants
        known = {
            1.0: '1', 2.0: '2', 0.5: '1/2',
            1.618033988749895: 'φ (golden ratio)',
            2.718281828459045: 'e',
            3.141592653589793: 'π',
        }
        label = None
        for val, name in known.items():
            if abs(limit - val) < 0.001:
                label = name
                break
        if label is None:
            label = f"≈ {limit:.6f}"
        
        conjectures.append(Conjecture(
            f"{name_a}(n) / {name_b}(n) → {label} as n → ∞",
            'ratio', len(ratios), 0.8
        ))
    
    return conjectures


def detect_modular_patterns(seq, name, depth=50):
    """Find modular regularities in a sequence."""
    conjectures = []
    n = min(len(seq), depth)
    
    for m in [2, 3, 4, 5, 6, 7, 8, 9, 10, 12]:
        residues = [seq[i] % m for i in range(n)]
        unique = set(residues)
        
        # If the sequence only hits a subset of residues
        if len(unique) < m // 2 and n > 10:
            conjectures.append(Conjecture(
                f"{name}(n) mod {m} ∈ {sorted(unique)} for n = 1..{n}",
                'modular', n, 0.7
            ))
        
        # Check periodicity of residues
        for period in range(1, min(13, n // 3)):
            periodic = True
            for i in range(period, n):
                if residues[i] != residues[i % period]:
                    periodic = False
                    break
            if periodic and period < m:
                conjectures.append(Conjecture(
                    f"{name}(n) mod {m} has period {period}: {residues[:period]}",
                    'modular', n, 0.85
                ))
                break  # smallest period found
    
    return conjectures


def detect_growth_rate(seq, name, depth=50):
    """Classify the growth rate of a sequence."""
    conjectures = []
    n = min(len(seq), depth)
    if n < 10:
        return conjectures
    
    vals = [abs(seq[i]) for i in range(n) if seq[i] > 0]
    if len(vals) < 8:
        return conjectures
    
    # Check for polynomial growth: look at successive ratios of differences
    diffs = [vals[i+1] - vals[i] for i in range(len(vals)-1)]
    if all(d > 0 for d in diffs[-5:]):
        # Positive differences. Check if d(n)/n^k converges
        for degree in range(1, 5):
            ratios = []
            for i in range(max(3, len(vals)//2), len(vals)):
                if i > 0:
                    ratios.append(vals[i] / (i ** degree))
            if ratios and max(ratios) - min(ratios) < 0.1 * (abs(ratios[0]) + 0.01):
                avg = sum(ratios) / len(ratios)
                conjectures.append(Conjecture(
                    f"{name}(n) ~ {avg:.4f} · n^{degree}",
                    'growth', len(ratios), 0.75
                ))
                break
    
    # Check for exponential growth
    if all(v > 0 for v in vals[1:]):
        log_ratios = [vals[i+1] / vals[i] for i in range(len(vals)-1) if vals[i] > 0]
        if log_ratios and len(log_ratios) > 5:
            recent = log_ratios[-5:]
            if max(recent) - min(recent) < 0.01 * recent[0]:
                base = sum(recent) / len(recent)
                if base > 1.01:
                    conjectures.append(Conjecture(
                        f"{name}(n) grows exponentially with base ≈ {base:.6f}",
                        'growth', len(recent), 0.8
                    ))
    
    return conjectures


def detect_sum_identities(seq, name, depth=50):
    """Look for identities involving partial sums."""
    conjectures = []
    n = min(len(seq), depth)
    
    partial_sums = []
    s = 0
    for i in range(n):
        s += seq[i]
        partial_sums.append(s)
    
    # Check if partial sums match another known sequence
    for other_name, gen in SEQUENCES.items():
        if other_name == name:
            continue
        other = gen(n)
        
        # Direct match: sum(a(1)..a(n)) = other(n)?
        matches = sum(1 for i in range(n) if partial_sums[i] == other[i])
        if matches == n and n > 5:
            conjectures.append(Conjecture(
                f"Σ {name}(k) for k=1..n = {other_name}(n)",
                'identity', n, 0.95
            ))
    
    # Check if partial sums are polynomial in n
    for degree in range(1, 5):
        # Test if sum = c * n^degree by checking ratio
        ratios = []
        for i in range(max(3, n//2), n):
            if (i+1) ** degree != 0:
                ratios.append(partial_sums[i] / ((i+1) ** degree))
        if ratios and max(ratios) - min(ratios) < 0.001 * (abs(ratios[0]) + 0.001):
            avg = sum(ratios) / len(ratios)
            # Try to express as simple fraction
            frac = Fraction(partial_sums[-1], n ** degree) if n ** degree != 0 else None
            if frac and frac.denominator < 100:
                conjectures.append(Conjecture(
                    f"Σ {name}(k) for k=1..n ≈ ({frac}) · n^{degree}",
                    'identity', len(ratios), 0.85
                ))
    
    return conjectures


def detect_recurrence(seq, name, depth=50):
    """Try to find a linear recurrence relation."""
    conjectures = []
    n = min(len(seq), depth)
    
    # Try recurrences of order 1-4
    for order in range(1, 5):
        if n < order * 3:
            continue
        
        # Check a(n) = c1*a(n-1) + c2*a(n-2) + ...
        # Simple case: constant coefficient
        if order == 1 and all(seq[i] != 0 for i in range(n-1)):
            ratios = [Fraction(seq[i+1], seq[i]) for i in range(n-1) if seq[i] != 0]
            if ratios and all(r == ratios[0] for r in ratios):
                conjectures.append(Conjecture(
                    f"{name}(n) = {ratios[0]} · {name}(n-1) [geometric]",
                    'recurrence', n, 0.95
                ))
        
        # a(n) = a(n-1) + a(n-2)?
        if order == 2 and n > 6:
            fib_like = all(
                seq[i] == seq[i-1] + seq[i-2]
                for i in range(2, n)
            )
            if fib_like:
                conjectures.append(Conjecture(
                    f"{name}(n) = {name}(n-1) + {name}(n-2) [Fibonacci-like]",
                    'recurrence', n - 2, 0.95
                ))
    
    return conjectures


# ─── Verification ────────────────────────────────────────────────────

def extend_and_verify(conjecture, extra=100):
    """Try to falsify a conjecture with more data."""
    # This is a stub for now — real verification would parse the
    # conjecture and generate additional test cases
    return conjecture


# ─── Discovery Engine ────────────────────────────────────────────────

class ConjectureEngine:
    """The core discovery loop."""
    
    def __init__(self, depth=60):
        self.depth = depth
        self.conjectures = []
        self.sequences = {}
    
    def generate_sequences(self):
        """Generate all named sequences."""
        for name, gen in SEQUENCES.items():
            try:
                self.sequences[name] = gen(self.depth)
            except Exception:
                pass
    
    def search_pairwise(self):
        """Search for relationships between all pairs of sequences."""
        names = list(self.sequences.keys())
        
        for i, name_a in enumerate(names):
            for name_b in names[i+1:]:
                seq_a = self.sequences[name_a]
                seq_b = self.sequences[name_b]
                
                self.conjectures.extend(
                    detect_divisibility(seq_a, seq_b, name_a, name_b, self.depth))
                self.conjectures.extend(
                    detect_divisibility(seq_b, seq_a, name_b, name_a, self.depth))
                self.conjectures.extend(
                    detect_inequality(seq_a, seq_b, name_a, name_b, self.depth))
                self.conjectures.extend(
                    detect_ratio_convergence(seq_a, seq_b, name_a, name_b, self.depth))
    
    def search_individual(self):
        """Search for patterns within each sequence."""
        for name, seq in self.sequences.items():
            self.conjectures.extend(detect_modular_patterns(seq, name, self.depth))
            self.conjectures.extend(detect_growth_rate(seq, name, self.depth))
            self.conjectures.extend(detect_sum_identities(seq, name, self.depth))
            self.conjectures.extend(detect_recurrence(seq, name, self.depth))
    
    def deduplicate(self):
        """Remove duplicate conjectures."""
        seen = set()
        unique = []
        for c in self.conjectures:
            if c.statement not in seen:
                seen.add(c.statement)
                unique.append(c)
        self.conjectures = unique
    
    def rank(self):
        """Sort conjectures by interestingness."""
        def score(c):
            kind_bonus = {
                'identity': 1.0, 'recurrence': 0.9, 'ratio': 0.8,
                'divisibility': 0.7, 'growth': 0.6,
                'inequality': 0.4, 'modular': 0.5
            }
            return c.confidence * kind_bonus.get(c.kind, 0.5)
        
        self.conjectures.sort(key=score, reverse=True)
    
    def discover(self):
        """Run the full discovery pipeline."""
        self.generate_sequences()
        self.search_pairwise()
        self.search_individual()
        self.deduplicate()
        self.rank()
        return self.conjectures
    
    def report(self, top_n=30):
        """Generate a human-readable report."""
        lines = []
        lines.append("═" * 70)
        lines.append("  CONJECTURE ENGINE — Automated Mathematical Discovery")
        lines.append("═" * 70)
        lines.append("")
        lines.append(f"Sequences analyzed: {len(self.sequences)}")
        lines.append(f"Conjectures found: {len(self.conjectures)}")
        lines.append("")
        
        by_kind = defaultdict(list)
        for c in self.conjectures:
            by_kind[c.kind].append(c)
        
        for kind in ['identity', 'recurrence', 'ratio', 'divisibility', 
                      'growth', 'modular', 'inequality']:
            group = by_kind.get(kind, [])
            if not group:
                continue
            lines.append(f"── {kind.upper()} ({len(group)}) ──")
            lines.append("")
            for c in group[:top_n]:
                marker = "✓" if c.confidence > 0.9 else "?" if c.confidence > 0.7 else "~"
                lines.append(f"  {marker} {c.statement}")
                lines.append(f"    [{c.evidence} cases, confidence {c.confidence:.2f}]")
                lines.append("")
        
        lines.append("═" * 70)
        return '\n'.join(lines)


# ─── Main ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    engine = ConjectureEngine(depth=60)
    results = engine.discover()
    print(engine.report())
    
    print(f"\nTotal: {len(results)} conjectures discovered.")
    
    # Highlight the most surprising findings
    surprising = [c for c in results if c.confidence > 0.85 and c.kind in ('identity', 'ratio')]
    if surprising:
        print(f"\n★ Most interesting ({len(surprising)}):")
        for c in surprising[:5]:
            print(f"  → {c.statement}")