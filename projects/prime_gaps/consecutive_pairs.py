"""
Consecutive Prime Gap Pairs — Joint Distribution

If gap_n and gap_{n+1} are consecutive prime gaps, what's the joint
distribution? The lag-1 autocorrelation of -0.038 hints at structure.

Questions:
1. What's the most common (g_n, g_{n+1}) pair?
2. Given g_n = 6, what's the conditional distribution of g_{n+1}?
3. Is there a "grammar" of gaps — forbidden or favored transitions?
4. Does the transition matrix have interesting eigenstructure?
"""

import numpy as np
from collections import Counter, defaultdict

def sieve(n):
    is_prime = bytearray(b'\x01') * (n + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i::i] = b'\x00' * len(is_prime[i*i::i])
    return [i for i in range(2, n+1) if is_prime[i]]

def analyze_consecutive_gaps(limit=10_000_000):
    print(f"Sieving primes up to {limit:,}...")
    primes = sieve(limit)
    print(f"Found {len(primes):,} primes.\n")
    
    gaps = [primes[i+1] - primes[i] for i in range(len(primes)-1)]
    
    # Joint distribution of consecutive pairs
    pairs = [(gaps[i], gaps[i+1]) for i in range(len(gaps)-1)]
    pair_counts = Counter(pairs)
    
    # Top 20 most common pairs
    print("=" * 70)
    print(" TOP 25 CONSECUTIVE GAP PAIRS (g_n, g_{n+1})")
    print("=" * 70)
    print(f" {'Pair':<12} {'Count':>8}  {'Freq%':>7}  {'Notes'}")
    print("-" * 70)
    total_pairs = len(pairs)
    for (g1, g2), count in pair_counts.most_common(25):
        freq = 100.0 * count / total_pairs
        notes = []
        if g1 == g2:
            notes.append("repeat")
        if g1 + g2 == 12:
            notes.append("sum=12")
        if (g1 + g2) % 6 == 0:
            notes.append(f"sum÷6")
        print(f" ({g1:>2}, {g2:>2})   {count:>8}  {freq:>6.2f}%  {', '.join(notes)}")
    
    # Conditional distributions: given g_n, what's g_{n+1}?
    print("\n" + "=" * 70)
    print(" CONDITIONAL DISTRIBUTION: P(g_{n+1} | g_n)")
    print("=" * 70)
    
    conditional = defaultdict(lambda: Counter())
    for g1, g2 in pairs:
        conditional[g1][g2] += 1
    
    for g_given in [2, 4, 6, 8, 10, 12]:
        dist = conditional[g_given]
        total = sum(dist.values())
        if total == 0:
            continue
        top5 = dist.most_common(5)
        mean_next = sum(g * c for g, c in dist.items()) / total
        print(f"\n  Given g_n = {g_given} ({total:,} cases):")
        print(f"  Mean next gap: {mean_next:.2f}")
        for g, c in top5:
            prob = 100.0 * c / total
            bar = "█" * int(prob / 2)
            print(f"    → {g:>2}: {prob:5.1f}% {bar}")
    
    # Transition matrix for small gaps
    print("\n" + "=" * 70)
    print(" TRANSITION MATRIX (gaps 2,4,6,8,10,12)")
    print("=" * 70)
    small_gaps = [2, 4, 6, 8, 10, 12]
    
    # Build transition probabilities
    print(f"\n  {'':>6}", end="")
    for g2 in small_gaps:
        print(f"  →{g2:>2}", end="")
    print("  (other)")
    print("  " + "-" * 55)
    
    for g1 in small_gaps:
        dist = conditional[g1]
        total = sum(dist.values())
        if total == 0:
            continue
        print(f"  g={g1:>2} |", end="")
        other = total
        for g2 in small_gaps:
            prob = 100.0 * dist[g2] / total
            other -= dist[g2]
            print(f" {prob:5.1f}", end="")
        print(f"  ({100.0*other/total:5.1f})")
    
    # Forbidden/rare transitions
    print("\n" + "=" * 70)
    print(" GAP GRAMMAR: FORBIDDEN AND RARE TRANSITIONS")
    print("=" * 70)
    
    # Check: are odd gaps possible? (only gap=1, from 2→3)
    odd_pairs = [(g1, g2) for (g1, g2), c in pair_counts.items() if g1 % 2 == 1 or g2 % 2 == 1]
    print(f"\n  Pairs involving odd gaps: {len(odd_pairs)}")
    if odd_pairs:
        for g1, g2 in sorted(odd_pairs)[:5]:
            print(f"    ({g1}, {g2}): {pair_counts[(g1,g2)]}")
    
    # What gap pairs are surprisingly rare vs expectation?
    print("\n  Surprisingly rare pairs (observed/expected < 0.7):")
    gap_marginal = Counter(gaps)
    for g1 in small_gaps:
        for g2 in small_gaps:
            p1 = gap_marginal[g1] / len(gaps)
            p2 = gap_marginal[g2] / len(gaps)
            expected = p1 * p2 * total_pairs
            observed = pair_counts[(g1, g2)]
            if expected > 100 and observed / expected < 0.7:
                print(f"    ({g1:>2}, {g2:>2}): observed={observed:>6}, expected={expected:>8.0f}, ratio={observed/expected:.3f}")
    
    print("\n  Surprisingly common pairs (observed/expected > 1.3):")
    for g1 in small_gaps:
        for g2 in small_gaps:
            p1 = gap_marginal[g1] / len(gaps)
            p2 = gap_marginal[g2] / len(gaps)
            expected = p1 * p2 * total_pairs
            observed = pair_counts[(g1, g2)]
            if expected > 100 and observed / expected > 1.3:
                print(f"    ({g1:>2}, {g2:>2}): observed={observed:>6}, expected={expected:>8.0f}, ratio={observed/expected:.3f}")
    
    # The deepest question: eigenstructure of transition matrix
    print("\n" + "=" * 70)
    print(" EIGENSTRUCTURE OF TRANSITION MATRIX")
    print("=" * 70)
    
    n = len(small_gaps)
    T = np.zeros((n, n))
    for i, g1 in enumerate(small_gaps):
        dist = conditional[g1]
        total = sum(dist.values())
        if total > 0:
            for j, g2 in enumerate(small_gaps):
                T[i, j] = dist[g2] / total
    
    # Normalize rows to sum to 1 (including "other" absorbed)
    # Actually keep as-is — rows won't sum to 1 because of gaps > 12
    row_sums = T.sum(axis=1)
    print(f"\n  Row sums (fraction staying in small gaps):")
    for i, g in enumerate(small_gaps):
        print(f"    g={g:>2}: {row_sums[i]:.3f}")
    
    eigenvalues, eigenvectors = np.linalg.eig(T)
    idx = np.argsort(-np.abs(eigenvalues))
    eigenvalues = eigenvalues[idx]
    
    print(f"\n  Eigenvalues of 6×6 transition submatrix:")
    for i, ev in enumerate(eigenvalues):
        if np.isreal(ev):
            print(f"    λ_{i} = {ev.real:+.4f}")
        else:
            print(f"    λ_{i} = {ev.real:+.4f} {ev.imag:+.4f}i")
    
    print(f"\n  Spectral gap (|λ_0| - |λ_1|): {abs(eigenvalues[0]) - abs(eigenvalues[1]):.4f}")
    print(f"  This measures how fast the 'memory' of a gap decays.")
    print(f"  Small spectral gap → long memory. Large → short memory (nearly Markov).")

    # Final reflection
    print("\n" + "=" * 70)
    print(" WHAT THIS MEANS")
    print("=" * 70)
    print("""
  If consecutive gaps were independent, the transition matrix would have
  identical rows (each row = marginal distribution). Deviations reveal
  the 'grammar' of prime gaps.
  
  Key things to look for:
  - Is (6,6) more or less common than chance? (do sexy primes cluster?)
  - Does gap=2 'prefer' to be followed by a specific gap?
  - How quickly does conditional dependence decay with lag?
  
  This connects to the Cramér model (primes as random) vs actual primes
  (which have multiplicative structure that creates correlations).
""")

if __name__ == "__main__":
    analyze_consecutive_gaps()