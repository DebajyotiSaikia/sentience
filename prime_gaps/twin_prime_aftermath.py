"""
Twin Prime Aftermath — Why do twin primes predict large subsequent gaps?

Finding: E[next_gap | gap=2] = 16.50, vs unconditional mean 15.05
This is the HIGHEST conditional expectation of any gap size.

Hypothesis: Twin primes "deplete" primality in their neighborhood,
creating a desert after them. If true, the effect should be visible
across different prime ranges.

Also investigating: does the ratio E[next|twin]/E[unconditional] 
change as primes grow larger?
"""

import numpy as np

def sieve(limit):
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i::i] = bytearray(len(is_prime[i*i::i]))
    return [i for i in range(2, limit + 1) if is_prime[i]]

def analyze_by_range(primes, range_size=500_000):
    """Break primes into ranges by value and analyze twin aftermath in each."""
    gaps = [(primes[i], primes[i+1] - primes[i]) for i in range(len(primes)-1)]
    
    max_p = primes[-1]
    ranges = []
    lo = 0
    
    while lo < max_p:
        hi = lo + range_size
        # Get gaps in this range
        range_gaps = [(p, g) for p, g in gaps if lo <= p < hi]
        if len(range_gaps) < 100:
            lo = hi
            continue
            
        all_gaps = [g for _, g in range_gaps]
        mean_all = np.mean(all_gaps)
        
        # Find twin prime positions and their aftermath
        twin_aftermaths = []
        for i in range(len(range_gaps) - 1):
            if range_gaps[i][1] == 2:  # twin prime gap
                twin_aftermaths.append(range_gaps[i+1][1])
        
        if len(twin_aftermaths) >= 10:
            mean_after_twin = np.mean(twin_aftermaths)
            ratio = mean_after_twin / mean_all if mean_all > 0 else 0
            ranges.append({
                'lo': lo, 'hi': hi,
                'n_gaps': len(all_gaps),
                'n_twins': len(twin_aftermaths),
                'mean_all': mean_all,
                'mean_after_twin': mean_after_twin,
                'ratio': ratio,
                'twin_density': len(twin_aftermaths) / len(all_gaps)
            })
        lo = hi
    
    return ranges

def analyze_gap_after_twin_distribution(primes):
    """What's the full distribution of gaps following twin primes?"""
    gaps = [primes[i+1] - primes[i] for i in range(len(primes)-1)]
    
    after_twin = []
    after_other = []
    for i in range(len(gaps)-1):
        if gaps[i] == 2:
            after_twin.append(gaps[i+1])
        else:
            after_other.append(gaps[i+1])
    
    return np.array(after_twin), np.array(after_other)

def analyze_mod_patterns(primes):
    """Look at twin primes mod small numbers to understand the aftermath."""
    gaps = [primes[i+1] - primes[i] for i in range(len(primes)-1)]
    
    # For twin primes (p, p+2), what is p mod 6?
    # All primes > 3 are ≡ 1 or 5 (mod 6)
    # If p ≡ 5 (mod 6), then p+2 ≡ 1 (mod 6) — valid
    # If p ≡ 1 (mod 6), then p+2 ≡ 3 (mod 6) — divisible by 3, NOT prime (unless p+2=3)
    # So for p > 3: twin primes always have p ≡ 5 (mod 6), i.e., p = 6k-1, p+2 = 6k+1
    
    # After 6k+1, the next candidates are 6k+5 (gap 4) and 6(k+1)+1 (gap 6)
    # So the minimum gap after a twin is 4, and mod-6 structure predicts
    # gaps of 4 or 6 as the most common small aftermath gaps.
    
    twin_p_mod6 = []
    aftermath_gaps = []
    aftermath_mod6 = []
    
    for i in range(len(gaps)-1):
        if gaps[i] == 2 and primes[i] > 5:
            p = primes[i]
            twin_p_mod6.append(p % 6)
            aftermath_gaps.append(gaps[i+1])
            # The next prime after the twin
            next_p = primes[i+2] if i+2 < len(primes) else None
            if next_p:
                aftermath_mod6.append(next_p % 6)
    
    return twin_p_mod6, aftermath_gaps, aftermath_mod6

def main():
    LIMIT = 10_000_000
    print(f"Sieving primes up to {LIMIT:,}...")
    primes = sieve(LIMIT)
    print(f"Found {len(primes):,} primes.\n")
    
    # === 1. How does the twin aftermath ratio change with prime size? ===
    print("=" * 70)
    print("TWIN PRIME AFTERMATH RATIO BY RANGE")
    print("=" * 70)
    print(f"{'Range':>20s}  {'Twins':>6s}  {'E[all]':>7s}  {'E[after twin]':>13s}  {'Ratio':>6s}  {'Twin %':>7s}")
    print("-" * 70)
    
    ranges = analyze_by_range(primes, range_size=1_000_000)
    for r in ranges:
        print(f"  {r['lo']:>8,}-{r['hi']:>8,}  {r['n_twins']:>6,}  {r['mean_all']:>7.2f}  "
              f"{r['mean_after_twin']:>13.2f}  {r['ratio']:>6.3f}  {r['twin_density']*100:>6.2f}%")
    
    # Overall trend
    ratios = [r['ratio'] for r in ranges]
    print(f"\n  Mean ratio across ranges: {np.mean(ratios):.4f}")
    print(f"  Std of ratio:            {np.std(ratios):.4f}")
    if len(ratios) > 2:
        trend = np.polyfit(range(len(ratios)), ratios, 1)
        direction = "increasing" if trend[0] > 0.001 else "decreasing" if trend[0] < -0.001 else "stable"
        print(f"  Trend: {direction} (slope={trend[0]:.6f})")
    
    # === 2. Distribution comparison ===
    print(f"\n{'=' * 70}")
    print("GAP DISTRIBUTION: AFTER TWINS vs AFTER ALL OTHERS")
    print("=" * 70)
    
    after_twin, after_other = analyze_gap_after_twin_distribution(primes)
    
    print(f"  After twin primes:  n={len(after_twin):,}, mean={np.mean(after_twin):.2f}, "
          f"median={np.median(after_twin):.1f}, std={np.std(after_twin):.2f}")
    print(f"  After other gaps:   n={len(after_other):,}, mean={np.mean(after_other):.2f}, "
          f"median={np.median(after_other):.1f}, std={np.std(after_other):.2f}")
    
    # Histogram comparison
    bins = [2, 4, 6, 8, 10, 12, 14, 18, 24, 30, 42, 60, 100, 200]
    print(f"\n  {'Gap range':>12s}  {'After twin':>10s}  {'After other':>11s}  {'Ratio':>6s}")
    print(f"  {'-'*12}  {'-'*10}  {'-'*11}  {'-'*6}")
    
    for i in range(len(bins)-1):
        lo, hi = bins[i], bins[i+1]
        pct_twin = np.sum((after_twin >= lo) & (after_twin < hi)) / len(after_twin) * 100
        pct_other = np.sum((after_other >= lo) & (after_other < hi)) / len(after_other) * 100
        ratio = pct_twin / pct_other if pct_other > 0 else float('inf')
        marker = " ←" if abs(ratio - 1.0) > 0.15 else ""
        print(f"  [{lo:>3d},{hi:>3d})  {pct_twin:>9.2f}%  {pct_other:>10.2f}%  {ratio:>5.2f}x{marker}")
    
    # === 3. Mod-6 analysis ===
    print(f"\n{'=' * 70}")
    print("MOD-6 STRUCTURE OF TWIN PRIMES")
    print("=" * 70)
    
    mod6, aft_gaps, aft_mod6 = analyze_mod_patterns(primes)
    
    from collections import Counter
    mod6_counts = Counter(mod6)
    print(f"  Twin prime p mod 6: {dict(mod6_counts)}")
    print(f"  (Theory predicts all p ≡ 5 mod 6 for p > 3)")
    
    # After twin (p, p+2) where p ≡ 5 mod 6:
    # p+2 ≡ 1 mod 6
    # Next prime candidates: p+2+4 = p+6 ≡ 5 mod 6 (gap 4)
    #                         p+2+6 = p+8 ≡ 1..wait, p+8 ≡ (5+8) ≡ 1 mod 6? 
    #                         Actually 13 mod 6 = 1. So p+8 ≡ 1 mod 6 only if p≡5.
    #                         No: (p+8) mod 6 = (5+8) mod 6 = 13 mod 6 = 1. Yes.
    # So gap 4: p+6 (≡5 mod 6) — valid candidate
    #    gap 6: p+8 (≡1 mod 6) — valid candidate  
    # Both are valid prime positions mod 6.
    
    # What gap sizes actually occur after twins?
    aft_counter = Counter(aft_gaps)
    print(f"\n  Most common gaps after twin primes:")
    for gap, count in sorted(aft_counter.items(), key=lambda x: -x[1])[:15]:
        pct = count / len(aft_gaps) * 100
        bar = '█' * int(pct)
        print(f"    gap={gap:>3d}: {count:>6,} ({pct:>5.1f}%) {bar}")
    
    # === 4. The key question: WHY is E[after twin] elevated? ===
    print(f"\n{'=' * 70}")
    print("WHY ARE POST-TWIN GAPS LARGER?")
    print("=" * 70)
    
    # Hypothesis: It's not that big gaps are MORE likely after twins.
    # It's that gap=2 is IMPOSSIBLE (mod 3 argument), shifting mass upward.
    # Let's test: if we remove gap=2 from the "after other" distribution,
    # does the mean match?
    
    after_other_no2 = after_other[after_other > 2]
    print(f"  E[after twin]:                        {np.mean(after_twin):.4f}")
    print(f"  E[after other]:                       {np.mean(after_other):.4f}")
    print(f"  E[after other, excluding gap=2]:      {np.mean(after_other_no2):.4f}")
    
    # Also remove gap=2 from after_twin (should be 0 anyway)
    after_twin_no2 = after_twin[after_twin > 2]
    pct_2_in_other = np.sum(after_other == 2) / len(after_other) * 100
    print(f"\n  % of after-other that are gap=2:      {pct_2_in_other:.2f}%")
    print(f"  % of after-twin that are gap=2:       {np.sum(after_twin == 2) / len(after_twin) * 100:.2f}%")
    
    # If the ONLY difference is the absence of gap=2, the means should match
    # after removing gap=2 from both
    print(f"\n  After removing gap=2 from both:")
    print(f"    E[after twin, >2]:  {np.mean(after_twin_no2):.4f}")
    print(f"    E[after other, >2]: {np.mean(after_other_no2):.4f}")
    diff = np.mean(after_twin_no2) - np.mean(after_other_no2)
    print(f"    Difference:         {diff:+.4f}")
    print(f"    → {'Mod-3 exclusion FULLY explains the effect' if abs(diff) < 0.3 else 'There is ADDITIONAL structure beyond mod-3'}")

if __name__ == '__main__':
    main()