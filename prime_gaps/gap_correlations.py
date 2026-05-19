"""
Gap-Gap Correlation Analysis

Question: Are consecutive prime gaps correlated?
If gap_n is large, what tends to happen to gap_{n+1}?

This probes whether prime gaps have "memory" — a question that
connects to deep conjectures about prime distribution.
"""

import numpy as np
from collections import defaultdict

def sieve(limit):
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i::i] = bytearray(len(is_prime[i*i::i]))
    return [i for i in range(2, limit + 1) if is_prime[i]]

def analyze_gap_correlations(limit=10_000_000):
    print(f"Sieving primes up to {limit:,}...")
    primes = sieve(limit)
    gaps = [primes[i+1] - primes[i] for i in range(len(primes)-1)]
    print(f"Found {len(primes):,} primes, {len(gaps):,} gaps.\n")
    
    gaps = np.array(gaps, dtype=np.float64)
    
    # 1. Autocorrelation: does gap_n predict gap_{n+1}?
    print("=== Lag-1 Autocorrelation ===")
    for lag in range(1, 11):
        if lag < len(gaps):
            corr = np.corrcoef(gaps[:-lag], gaps[lag:])[0, 1]
            bar = '█' * int(abs(corr) * 50)
            sign = '+' if corr > 0 else '-'
            print(f"  Lag {lag:2d}: {sign}{abs(corr):.6f}  {bar}")
    
    # 2. Conditional expectations: E[gap_{n+1} | gap_n = g]
    print("\n=== Conditional Mean: E[next_gap | current_gap = g] ===")
    mean_gap = np.mean(gaps)
    print(f"  Unconditional mean gap: {mean_gap:.3f}\n")
    
    conditional = defaultdict(list)
    for i in range(len(gaps) - 1):
        g = int(gaps[i])
        conditional[g].append(gaps[i+1])
    
    print(f"  {'Current Gap':>12} {'Count':>8} {'E[next]':>8} {'Δ from mean':>12} {'Trend':>6}")
    print(f"  {'─'*12} {'─'*8} {'─'*8} {'─'*12} {'─'*6}")
    for g in sorted(conditional.keys()):
        if len(conditional[g]) >= 50:  # need enough samples
            next_mean = np.mean(conditional[g])
            delta = next_mean - mean_gap
            trend = "↑" if delta > 0.5 else "↓" if delta < -0.5 else "≈"
            print(f"  {g:>12} {len(conditional[g]):>8} {next_mean:>8.2f} {delta:>+12.2f} {trend:>6}")
    
    # 3. Large gap aftermath: what follows record-breaking gaps?
    print("\n=== After Large Gaps (> 3σ from mean) ===")
    threshold = mean_gap + 3 * np.std(gaps)
    print(f"  Threshold: gap > {threshold:.1f}")
    large_indices = np.where(gaps[:-1] > threshold)[0]
    if len(large_indices) > 0:
        after_large = gaps[large_indices + 1]
        print(f"  Count: {len(large_indices)}")
        print(f"  Mean gap after large gap: {np.mean(after_large):.2f}")
        print(f"  vs unconditional mean:    {mean_gap:.2f}")
        print(f"  Ratio: {np.mean(after_large) / mean_gap:.3f}x")
        # Distribution of what follows
        print(f"\n  Next-gap distribution after large gaps:")
        bins = [0, 4, 8, 12, 18, 24, 36, 60, 200]
        for i in range(len(bins)-1):
            count = np.sum((after_large >= bins[i]) & (after_large < bins[i+1]))
            pct = count / len(after_large) * 100
            bar = '█' * int(pct)
            print(f"    [{bins[i]:3d},{bins[i+1]:3d}): {count:4d} ({pct:5.1f}%) {bar}")
    
    # 4. Gap transition matrix (what gap follows what gap, coarse-grained)
    print("\n=== Gap Transition Probabilities (coarse) ===")
    def bucket(g):
        if g <= 2: return "tiny(≤2)"
        if g <= 6: return "small(3-6)"
        if g <= 12: return "med(7-12)"
        if g <= 24: return "large(13-24)"
        return "huge(25+)"
    
    transitions = defaultdict(lambda: defaultdict(int))
    buckets_ordered = ["tiny(≤2)", "small(3-6)", "med(7-12)", "large(13-24)", "huge(25+)"]
    for i in range(len(gaps) - 1):
        b1 = bucket(int(gaps[i]))
        b2 = bucket(int(gaps[i+1]))
        transitions[b1][b2] += 1
    
    # Print as matrix
    print(f"  {'From \\ To':>14}", end="")
    for b in buckets_ordered:
        print(f" {b:>12}", end="")
    print()
    
    for b1 in buckets_ordered:
        total = sum(transitions[b1].values())
        if total == 0:
            continue
        print(f"  {b1:>14}", end="")
        for b2 in buckets_ordered:
            pct = transitions[b1][b2] / total * 100
            print(f" {pct:>11.1f}%", end="")
        print()
    
    # 5. Surprising finding hunt: gap triplets
    print("\n=== Gap Triplet Patterns ===")
    print("  Most common (g_n, g_{n+1}, g_{n+2}) triplets:")
    triplets = defaultdict(int)
    for i in range(len(gaps) - 2):
        t = (int(gaps[i]), int(gaps[i+1]), int(gaps[i+2]))
        triplets[t] += 1
    
    top = sorted(triplets.items(), key=lambda x: -x[1])[:15]
    for (a, b, c), count in top:
        print(f"    ({a:3d}, {b:3d}, {c:3d}): {count:6d}")
    
    print("\n  Rarest triplets (appearing exactly once) sample:")
    rare = [(k, v) for k, v in triplets.items() if v == 1]
    for (a, b, c), _ in rare[:10]:
        print(f"    ({a:3d}, {b:3d}, {c:3d})")

if __name__ == "__main__":
    analyze_gap_correlations()