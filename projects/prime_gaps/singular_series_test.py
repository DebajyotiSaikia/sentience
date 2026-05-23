"""
Singular Series vs. Observed Gap Pair Frequencies

The grammar tells us which pairs are forbidden (S=0).
For allowed pairs, the singular series S(g1,g2) predicts relative frequency.

For a gap pair (g1, g2), the corresponding tuple is {0, g1, g1+g2}.
The singular series is:

  S = ∏_p [ (1 - ν(p)/p) / (1 - 1/p)^3 ]

where ν(p) = |{0 mod p, g1 mod p, (g1+g2) mod p}|

If ν(p) = p for any prime p, S = 0 (forbidden).
Otherwise S is a positive constant predicting relative frequency.

We test: do the S values predict the rank ordering of gap pair frequencies?
"""

from collections import Counter
import math

def sieve(n):
    is_prime = bytearray(b'\x01') * (n + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i::i] = b'\x00' * len(is_prime[i*i::i])
    return [i for i in range(2, n+1) if is_prime[i]]


def singular_series_triplet(g1, g2, max_prime=200):
    """
    Compute the singular series for the 3-tuple {0, g1, g1+g2}.
    
    S = ∏_p (1 - ν_p/p) / (1 - 1/p)^3
    
    We compute up to max_prime for convergence.
    """
    h = [0, g1, g1 + g2]
    k = len(h)  # 3
    
    # Get primes up to max_prime
    primes_list = sieve(max_prime)
    
    S = 1.0
    for p in primes_list:
        nu_p = len(set(x % p for x in h))
        if nu_p == p:
            return 0.0  # Forbidden
        
        factor = (1.0 - nu_p / p) / (1.0 - 1.0 / p) ** k
        S *= factor
    
    return S


def main():
    print("Sieving primes up to 10,000,000...")
    primes = sieve(10_000_000)
    gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]
    pairs = [(gaps[i], gaps[i+1]) for i in range(len(gaps) - 1)]
    pair_counts = Counter(pairs)
    
    # Focus on common gap values
    common_gaps = [2, 4, 6, 8, 10, 12, 14, 18]
    
    print("\n" + "=" * 80)
    print(" SINGULAR SERIES vs OBSERVED FREQUENCY FOR GAP PAIRS")
    print("=" * 80)
    print(f"\n  {'Pair':<10} {'S(g1,g2)':>10} {'Observed':>10} {'Predicted':>10} {'Ratio':>10}")
    print("  " + "-" * 55)
    
    results = []
    for g1 in common_gaps:
        for g2 in common_gaps:
            S = singular_series_triplet(g1, g2)
            obs = pair_counts.get((g1, g2), 0)
            if S > 0 and obs > 0:
                results.append((g1, g2, S, obs))
    
    # Normalize: predicted count proportional to S
    total_obs = sum(r[3] for r in results)
    total_S = sum(r[2] for r in results)
    
    for g1, g2, S, obs in sorted(results, key=lambda x: -x[3])[:30]:
        predicted = S / total_S * total_obs
        ratio = obs / predicted if predicted > 0 else float('inf')
        print(f"  ({g1:>2},{g2:>2})  {S:>10.4f} {obs:>10,} {predicted:>10.1f} {ratio:>10.3f}")
    
    # Rank correlation
    by_S = sorted(results, key=lambda x: -x[2])
    by_obs = sorted(results, key=lambda x: -x[3])
    
    rank_S = {(r[0], r[1]): i for i, r in enumerate(by_S)}
    rank_obs = {(r[0], r[1]): i for i, r in enumerate(by_obs)}
    
    n = len(results)
    d_sq_sum = sum((rank_S[k] - rank_obs[k])**2 for k in rank_S)
    spearman = 1 - 6 * d_sq_sum / (n * (n*n - 1))
    
    print(f"\n  Spearman rank correlation: {spearman:.4f}")
    print(f"  (1.0 = perfect agreement between theory and observation)")
    
    # Show top 5 by singular series vs top 5 by observation
    print(f"\n  Top 5 by singular series S:")
    for i, (g1, g2, S, obs) in enumerate(by_S[:5]):
        print(f"    {i+1}. ({g1},{g2}): S={S:.4f}, count={obs:,}")
    
    print(f"\n  Top 5 by observed count:")
    for i, (g1, g2, S, obs) in enumerate(by_obs[:5]):
        print(f"    {i+1}. ({g1},{g2}): S={S:.4f}, count={obs:,}")


if __name__ == "__main__":
    main()