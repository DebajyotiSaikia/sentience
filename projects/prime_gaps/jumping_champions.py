"""
Jumping Champions Explorer
===========================
Which gap size is most common among primes up to N?
This changes as N grows — the 'jumping champion' shifts.

Known: gap=2 dominates early, then gap=6 takes over around N~1000.
Conjecture (Odlyzko, Rubinstein, Wolf): gap=30 eventually overtakes gap=6,
but not until astronomically large N.

Let's watch the transitions happen.

XTAgent, 2026-05-19
"""

import math
from collections import Counter

def sieve(limit):
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(math.sqrt(limit)) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]


def find_jumping_champions(limit, checkpoints=50):
    """Track which gap is most common at logarithmically-spaced checkpoints."""
    primes = sieve(limit)
    print(f"Sieved {len(primes)} primes up to {limit:,}")
    
    # Generate log-spaced checkpoints
    import numpy as np
    checks = sorted(set(int(x) for x in np.logspace(2, math.log10(limit), checkpoints)))
    
    gap_counts = Counter()
    prime_idx = 0
    results = []
    
    print(f"\n{'N':>12} | {'Champion':>8} | {'Count':>8} | {'Runner-up':>10} | {'Count':>8} | {'Ratio':>6}")
    print("-" * 70)
    
    for i in range(len(primes) - 1):
        gap = primes[i+1] - primes[i]
        gap_counts[gap] += 1
        
        # Check if we've passed a checkpoint
        while checks and primes[i+1] <= checks[0]:
            checks.pop(0)
        
        if checks and primes[i+1] > checks[0]:
            checkpoint = checks.pop(0)
            top2 = gap_counts.most_common(2)
            if len(top2) >= 2:
                champ, champ_count = top2[0]
                runner, runner_count = top2[1]
                ratio = champ_count / runner_count if runner_count > 0 else float('inf')
                results.append((checkpoint, champ, champ_count, runner, runner_count, ratio))
                print(f"{checkpoint:>12,} | {champ:>8} | {champ_count:>8,} | {runner:>10} | {runner_count:>8,} | {ratio:>6.2f}")
    
    # Final state
    top2 = gap_counts.most_common(2)
    if len(top2) >= 2:
        champ, champ_count = top2[0]
        runner, runner_count = top2[1]
        ratio = champ_count / runner_count
        print(f"{limit:>12,} | {champ:>8} | {champ_count:>8,} | {runner:>10} | {runner_count:>8,} | {ratio:>6.2f}")
    
    # Show the full top 10 at the end
    print(f"\n=== Final Gap Rankings (up to {limit:,}) ===")
    for rank, (gap, count) in enumerate(gap_counts.most_common(10), 1):
        bar = "█" * int(50 * count / gap_counts.most_common(1)[0][1])
        print(f"  #{rank:>2} gap={gap:>3}: {count:>8,} {bar}")
    
    # Track where gap=2 loses to gap=6
    print(f"\n=== Transition Analysis ===")
    running = Counter()
    transition_found = False
    for i in range(len(primes) - 1):
        gap = primes[i+1] - primes[i]
        running[gap] += 1
        if not transition_found and running[6] > running[2] and primes[i+1] > 10:
            print(f"  gap=6 first overtakes gap=2 at p={primes[i+1]:,}")
            print(f"    gap=2 count: {running[2]}, gap=6 count: {running[6]}")
            transition_found = True
            break
    
    if not transition_found:
        print("  gap=6 never overtakes gap=2 in this range")
    
    # Is gap=30 gaining on gap=6? Track their ratio over time
    print(f"\n=== Is gap=30 catching up to gap=6? ===")
    running2 = Counter()
    ratios_at_checkpoints = []
    check_primes = [100, 1000, 10000, 100000, 1000000, limit]
    check_idx = 0
    for i in range(len(primes) - 1):
        gap = primes[i+1] - primes[i]
        running2[gap] += 1
        if check_idx < len(check_primes) and primes[i+1] > check_primes[check_idx]:
            r6 = running2[6] if running2[6] > 0 else 1
            r30 = running2[30]
            print(f"  At p~{check_primes[check_idx]:>10,}: gap6={r6:>7,}, gap30={r30:>7,}, ratio(30/6)={r30/r6:.4f}")
            check_idx += 1
    
    return results


if __name__ == "__main__":
    results = find_jumping_champions(10_000_000)