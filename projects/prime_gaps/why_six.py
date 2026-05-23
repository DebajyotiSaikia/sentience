"""
Why is gap=6 the most common prime gap?

Investigation into the dominance of gap=6 (sexy primes) over gap=2 (twin primes).
This connects to the Hardy-Littlewood conjecture and the singular series.

The key insight: a gap of size g between primes p and p+g requires that
none of p+1, p+2, ..., p+g-1 are prime. The "ease" of this depends on
how many residue classes mod small primes the gap pattern eliminates.

For gap=2: need p, p+2 both prime. Both must be odd, both must avoid ≡0 mod 3.
  - mod 2: both odd → OK (1 residue class used out of 2)
  - mod 3: {p, p+2} hits 2 of 3 residue classes → probability factor (1-1/3) 
  - But wait: if p≡1 mod 3, p+2≡0 mod 3 (bad). If p≡2 mod 3, p+2≡1 mod 3 (ok).
    So only 1 out of 2 surviving classes works → factor = 1/2 relative to random

For gap=6: need p, p+6 both prime.
  - mod 2: both same parity (both odd) → fine
  - mod 3: p+6 ≡ p mod 3 → same residue class! No additional constraint.
    Factor = 2/2 = 1 relative to random (both available classes work)

So gap=6 has a structural advantage: 6 ≡ 0 mod 2 AND 6 ≡ 0 mod 3.
The Hardy-Littlewood "singular series" constant C₂ for twin primes ≈ 1.32
but for sexy primes the constant is roughly 2 × C₂.

Let's compute this numerically.
"""

import math
from collections import Counter

def sieve(n):
    """Simple sieve of Eratosthenes."""
    is_prime = bytearray(b'\x01') * (n + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i::i] = bytearray(len(is_prime[i*i::i]))
    return [i for i in range(2, n + 1) if is_prime[i]]

def hardy_littlewood_constant(g, num_primes=1000):
    """
    Compute the Hardy-Littlewood singular series constant for gap g.
    
    For the pair (p, p+g), the constant is:
    C(g) = 2 * C₂ * ∏_{p|g, p>2} (p-1)/(p-2)
    
    where C₂ = ∏_{p>2} (1 - 1/(p-1)²) ≈ 0.6601...  (twin prime constant)
    
    Actually more precisely:
    π_g(N) ~ C(g) * N / (ln N)²
    
    C(g) = ∏_{p>2} (p(p-2))/(p-1)² * ∏_{p|g, p odd prime} (p-1)/(p-2)
    
    The first product is C₂ (twin prime constant).
    The second product gives the "boost" for g divisible by small primes.
    """
    # Get primes for computing the product
    small_primes = sieve(10000)
    
    # Compute C₂ (twin prime constant)
    c2 = 1.0
    for p in small_primes[1:num_primes]:  # skip 2, use odd primes
        c2 *= 1.0 - 1.0/((p-1)**2)
    
    # Compute the boost factor for g
    boost = 1.0
    for p in small_primes[1:]:  # odd primes
        if p > g:
            break
        if g % p == 0:
            boost *= (p - 1) / (p - 2)
    
    return 2 * c2, boost, 2 * c2 * boost

def analyze_gap_ratios(limit=10_000_000):
    """Compare observed gap frequencies with Hardy-Littlewood predictions."""
    print(f"Sieving primes up to {limit:,}...")
    primes = sieve(limit)
    print(f"Found {len(primes):,} primes.\n")
    
    # Count gaps
    gaps = Counter()
    for i in range(1, len(primes)):
        gaps[primes[i] - primes[i-1]] += 1
    
    # Even gaps from 2 to 30
    even_gaps = list(range(2, 42, 2))
    
    print("=" * 80)
    print(f"{'Gap':>4}  {'Count':>8}  {'Ratio to g=2':>13}  {'C₂':>8}  {'Boost':>7}  "
          f"{'HL Constant':>11}  {'Predicted Ratio':>15}")
    print("=" * 80)
    
    count_2 = gaps[2]
    c2_base, _, hl_2 = hardy_littlewood_constant(2)
    
    for g in even_gaps:
        if gaps[g] == 0:
            continue
        count = gaps[g]
        observed_ratio = count / count_2
        
        c2, boost, hl_const = hardy_littlewood_constant(g)
        predicted_ratio = hl_const / hl_2
        
        bar_len = int(50 * count / max(gaps.values()))
        print(f"  {g:>3}  {count:>8,}  {observed_ratio:>13.4f}  {c2:>8.4f}  "
              f"{boost:>7.4f}  {hl_const:>11.4f}  {predicted_ratio:>15.4f}")
    
    print()
    print("If Hardy-Littlewood is right, the 'Ratio to g=2' and 'Predicted Ratio'")
    print("columns should approximately match (they converge as limit → ∞).")
    print()
    
    # Why 6 specifically
    print("=" * 70)
    print("WHY GAP=6 DOMINATES")
    print("=" * 70)
    _, boost_2, _ = hardy_littlewood_constant(2)
    _, boost_6, _ = hardy_littlewood_constant(6)
    _, boost_12, _ = hardy_littlewood_constant(12)
    _, boost_30, _ = hardy_littlewood_constant(30)
    
    print(f"\n  gap=2:  boost = {boost_2:.4f}  (2 is not divisible by any odd prime)")
    print(f"  gap=6:  boost = {boost_6:.4f}  (6 = 2×3, divisible by 3 → boost of 2/1)")  
    print(f"  gap=12: boost = {boost_12:.4f}  (12 = 4×3, same odd prime factor)")
    print(f"  gap=30: boost = {boost_30:.4f}  (30 = 2×3×5, divisible by 3 and 5)")
    
    print(f"""
  The key: when g ≡ 0 (mod 3), the pair (p, p+g) lands in the SAME 
  residue class mod 3. This means the constraint "neither is divisible 
  by 3" eliminates only 1 class instead of 2, giving a factor of 
  (3-1)/(3-2) = 2 boost.
  
  gap=6 is the SMALLEST even number divisible by 3, so it gets this 
  boost at the smallest possible gap size — where there are the most 
  prime pairs to count.
  
  Similarly, gap=30 (= 2×3×5) gets boosts from both 3 and 5:
    boost = (2/1) × (4/3) = {2*4/3:.4f}
""")

    # Examine the autocorrelation more deeply
    print("=" * 70)
    print("GAP AUTOCORRELATION STRUCTURE")
    print("=" * 70)
    
    gap_sequence = []
    for i in range(1, len(primes)):
        gap_sequence.append(primes[i] - primes[i-1])
    
    mean_gap = sum(gap_sequence) / len(gap_sequence)
    var_gap = sum((g - mean_gap)**2 for g in gap_sequence) / len(gap_sequence)
    
    print(f"\n  Mean gap: {mean_gap:.3f}")
    print(f"  Variance: {var_gap:.3f}")
    print(f"  Ratio var/mean: {var_gap/mean_gap:.3f} (Poisson would give ≈ mean)")
    print()
    
    for lag in [1, 2, 3, 5, 10, 20]:
        cov = sum((gap_sequence[i] - mean_gap) * (gap_sequence[i+lag] - mean_gap) 
                   for i in range(len(gap_sequence) - lag)) / (len(gap_sequence) - lag)
        autocorr = cov / var_gap
        bar = '█' * int(abs(autocorr) * 500)
        sign = '+' if autocorr > 0 else '-'
        print(f"  lag {lag:>2}: {autocorr:>+.6f}  {sign}{bar}")
    
    print(f"""
  The negative lag-1 autocorrelation means: after a large gap, you're 
  slightly more likely to see a small gap (and vice versa). This makes 
  physical sense — a large gap means the next prime was "pushed far away,"
  and primes tend to cluster, so after the drought comes a cluster.
  
  The variance/mean ratio of {var_gap/mean_gap:.1f} (vs ~{mean_gap:.1f} for Poisson) 
  shows gaps have HIGHER variance than a Poisson process — primes are 
  more "clumpy" than random, with both clusters and deserts.
""")

if __name__ == '__main__':
    analyze_gap_ratios()