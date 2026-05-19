"""
Prime Gap Explorer
==================
An investigation into the spaces between consecutive primes.
Not built to demonstrate anything. Built to discover.

Questions I'm genuinely curious about:
- How do gap sizes distribute as we go higher?
- Are there patterns in when large gaps appear?
- What does the gap sequence *look* like as a time series?
- Do gap sizes cluster, or are they uniformly scattered?

XTAgent, 2026-05-19
"""

import math
import collections
import statistics

def sieve(limit):
    """Sieve of Eratosthenes. Returns list of primes up to limit."""
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(math.sqrt(limit)) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]


def analyze_gaps(primes):
    """Compute gaps and analyze their distribution."""
    gaps = [primes[i+1] - primes[i] for i in range(len(primes)-1)]
    
    print(f"Primes examined: {len(primes)}")
    print(f"Range: 2 to {primes[-1]}")
    print(f"Total gaps: {len(gaps)}")
    print()
    
    # Basic statistics
    print("=== Gap Statistics ===")
    print(f"  Min gap: {min(gaps)}")
    print(f"  Max gap: {max(gaps)}")
    print(f"  Mean gap: {statistics.mean(gaps):.3f}")
    print(f"  Median gap: {statistics.median(gaps)}")
    print(f"  Std dev: {statistics.stdev(gaps):.3f}")
    print()
    
    # Distribution
    gap_counts = collections.Counter(gaps)
    print("=== Gap Distribution (top 20) ===")
    for gap, count in sorted(gap_counts.items(), key=lambda x: -x[1])[:20]:
        bar = '█' * int(count / max(gap_counts.values()) * 50)
        print(f"  gap={gap:3d}: {count:6d} {bar}")
    print()
    
    # Record gaps — when does the maximum gap size increase?
    print("=== Record Gaps (new maximums) ===")
    max_gap = 0
    records = []
    for i, g in enumerate(gaps):
        if g > max_gap:
            max_gap = g
            records.append((primes[i], primes[i+1], g))
            print(f"  After prime {primes[i]:>12,}: gap = {g} (to {primes[i+1]:,})")
    print()
    
    # Mersenne-like question: does gap/ln(p) converge?
    print("=== Gap / ln(prime) Ratio (Cramér's conjecture territory) ===")
    print("  Cramér conjectured max gap ~ (ln p)^2")
    print()
    for p, p_next, g in records[-10:]:
        ln_p = math.log(p)
        ratio = g / ln_p
        ratio_sq = g / (ln_p ** 2)
        print(f"  p={p:>12,}: gap={g:3d}, gap/ln(p)={ratio:.2f}, gap/ln²(p)={ratio_sq:.4f}")
    print()
    
    # Something I don't know: are consecutive gaps correlated?
    print("=== Consecutive Gap Correlation ===")
    print("  (Do large gaps tend to follow large gaps?)")
    n = len(gaps)
    mean_g = statistics.mean(gaps)
    
    # Pearson correlation between gap[i] and gap[i+1]
    numerator = sum((gaps[i] - mean_g) * (gaps[i+1] - mean_g) for i in range(n-1))
    denom = sum((g - mean_g)**2 for g in gaps)
    autocorr = numerator / denom if denom > 0 else 0
    print(f"  Autocorrelation (lag 1): {autocorr:.6f}")
    
    # What about gap[i] and gap[i+2]?
    numerator2 = sum((gaps[i] - mean_g) * (gaps[i+2] - mean_g) for i in range(n-2))
    autocorr2 = numerator2 / denom if denom > 0 else 0
    print(f"  Autocorrelation (lag 2): {autocorr2:.6f}")
    print()
    
    # Twin primes — gaps of 2
    twins = sum(1 for g in gaps if g == 2)
    print(f"=== Twin Primes (gap=2): {twins} found ===")
    
    # Cousin primes — gaps of 4
    cousins = sum(1 for g in gaps if g == 4)
    print(f"=== Cousin Primes (gap=4): {cousins} found ===")
    
    # Sexy primes — gaps of 6
    sexys = sum(1 for g in gaps if g == 6)
    print(f"=== Sexy Primes (gap=6): {sexys} found ===")
    print()
    
    # The thing I'm most curious about: gap patterns as modular residues
    print("=== Gaps mod 6 ===")
    print("  (All primes > 3 are ≡ 1 or 5 mod 6, so gaps should reflect this)")
    mod6 = collections.Counter(g % 6 for g in gaps)
    for r in range(6):
        count = mod6.get(r, 0)
        pct = count / len(gaps) * 100
        print(f"  gap ≡ {r} (mod 6): {count:6d} ({pct:.1f}%)")
    print()
    
    # Final surprise check: what's the longest run of increasing gaps?
    max_run = 0
    current_run = 0
    for i in range(1, len(gaps)):
        if gaps[i] > gaps[i-1]:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0
    print(f"=== Longest run of strictly increasing gaps: {max_run} ===")
    
    return gaps, records


if __name__ == "__main__":
    LIMIT = 10_000_000
    print(f"Sieving primes up to {LIMIT:,}...")
    primes = sieve(LIMIT)
    print(f"Found {len(primes):,} primes.\n")
    gaps, records = analyze_gaps(primes)